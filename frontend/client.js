// client.js – STT → backend + UI refresh with debug and manual start

// ===== debug helper =====
function log(...args) { console.log("[DEBUG]", ...args); }

// WebSocket connection
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = evt => {
  const { summary, colours, debug } = JSON.parse(evt.data);
  log("Pipeline debug:", debug);
  document.getElementById("summary").textContent = summary;
  if (colours["A"]) setColour("colA", colours["A"]);
  if (colours["B"]) setColour("colB", colours["B"]);
};

// Helper to set the color circles
function setColour(id, [r, g, b]) {
  document.getElementById(id).style.background = `rgb(${r},${g},${b})`;
}

// Check for browser support
if (!("SpeechRecognition" in window) && !("webkitSpeechRecognition" in window)) {
  alert(
    "Web Speech API not supported in this browser. " +
    "Please open this page in Chrome or Edge."
  );
}

// --- quick-and-dirty browser STT setup ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const rec = new SpeechRecognition();
rec.continuous = true;
rec.interimResults = false;

// Debug callbacks
rec.onstart    = () => log("Speech recognition started");
rec.onerror    = e  => { console.error("STT error:", e.error); alert("STT error: " + e.error); };
rec.onaudioend = () => log("Audio end (silence)");
rec.onend      = () => log("Speech recognition ended");

// Base timestamp for word timing
let t0 = performance.now() / 1000;

// On speech result, extract words with timestamps and send to server
rec.onresult = e => {
  const words = [];
  for (let i = e.resultIndex; i < e.results.length; i++) {
    const txt = e.results[i][0].transcript.trim();
    txt.split(/\s+/).forEach(w => {
      const now = performance.now() / 1000 - t0;
      words.push([w.toLowerCase(), now]);
    });
  }
  log("Sending words:", words);
  ws.send(JSON.stringify({ user: "A", words }));
};

// Start recognition only on button click
document.getElementById("startBtn").addEventListener("click", () => {
  try {
    rec.start();
  } catch (e) {
    console.error("rec.start() failed:", e);
  }
});