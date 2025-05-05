/*  client.js
    – local STT + emotion UI
    – WebRTC peer video (signalling over the same WS)
*/

const qs     = new URLSearchParams(location.search);
const me     = (qs.get("user") || prompt("Enter your ID (A or B)")).trim().toUpperCase();
if (!["A","B"].includes(me)) alert("Use A or B") || location.reload();

const summaryEl = document.getElementById("summary");
const leftCol   = document.getElementById("colLeft");
const rightCol  = document.getElementById("colRight");
const leftVid   = document.getElementById("vidLeft");
const rightVid  = document.getElementById("vidRight");
const startBtn  = document.getElementById("startBtn");

// ----------------  WebSocket ----------------
const proto = location.protocol === "https:" ? "wss" : "ws";
const ws    = new WebSocket(`${proto}://${location.host}/ws`);

ws.onmessage = ({data}) => {
  const msg = JSON.parse(data);

  // 1) UI payload (summary + colours)
  if (msg.kind === "ui") {
    const { summary, colours } = msg;
    summaryEl.textContent = summary;
    if (colours.B) setColour(leftCol,  colours.B);   // left  → user B
    if (colours.A) setColour(rightCol, colours.A);   // right → user A
  }

  // 2) signalling for WebRTC
  if (msg.kind === "signal") handleSignal(msg.data);
};

function setColour(el, [r,g,b]) {
  el.style.background = `rgb(${r},${g},${b})`;
}

// ----------------  WebRTC ----------------
const pc = new RTCPeerConnection({
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
});

pc.onicecandidate = ({ candidate }) => {
  if (candidate) ws.send(JSON.stringify({ signal: { candidate } }));
};

pc.ontrack = ({ streams: [remote] }) => {
  if (me === "A")       leftVid.srcObject  = remote;  // B on the left
  else /* me === "B" */ rightVid.srcObject = remote;  // A on the right
};

// --- NEW: queue ICE until we have a remote description -------------
let remoteDescSet = false;
const pendingICE  = [];

async function handleSignal(data) {
  // 1) remote SDP
  if (data.sdp) {
    await pc.setRemoteDescription(data.sdp);
    remoteDescSet = true;

    // flush any candidates that arrived early
    for (const c of pendingICE) await pc.addIceCandidate(c);
    pendingICE.length = 0;

    if (data.sdp.type === "offer") {
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      ws.send(JSON.stringify({ signal: { sdp: pc.localDescription } }));
    }
    return;
  }

  // 2) remote ICE candidate
  if (data.candidate) {
    if (remoteDescSet) {
      await pc.addIceCandidate(data.candidate);
    } else {
      pendingICE.push(data.candidate);
    }
  }
}

// ----------------  Local media ----------------
navigator.mediaDevices.getUserMedia({ video:true, audio:false })
  .then(async stream => {
    // attach own camera to correct side
    if (me === "A")        rightVid.srcObject = stream;
    else /* me === "B" */  leftVid.srcObject  = stream;

    // send tracks to peer
    stream.getTracks().forEach(t => pc.addTrack(t, stream));

    // decide the initiator: user A always begins
    if (me === "A") {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      ws.send(JSON.stringify({ signal:{sdp: pc.localDescription} }));
    }
  })
  .catch(err => { console.error(err); alert("Camera access failed"); });

// ----------------  Speech-to-text ----------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) alert("Open in Chrome / Edge for microphone support.");

const rec = new SpeechRecognition();
rec.continuous     = true;
rec.interimResults = false;

let t0 = performance.now()/1000;
rec.onresult = ev => {
  const words = [];
  for (let i=ev.resultIndex; i<ev.results.length; i++) {
    ev.results[i][0].transcript.trim().split(/\s+/).forEach(w=>{
      words.push([w.toLowerCase(), performance.now()/1000 - t0]);
    });
  }
  ws.send(JSON.stringify({ user: me, words }));
};

startBtn.onclick = () => { try { rec.start(); } catch(e){} };

// clean-up on close / reload
window.addEventListener("beforeunload", ()=>{ ws.close(); pc.close(); });