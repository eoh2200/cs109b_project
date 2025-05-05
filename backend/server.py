from pathlib import Path
import asyncio, json, logging
from collections import deque, defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from .utils import rgb_for, average_rgb
from .segmentation  import split_utterances
from .models        import summarizer, emotion_cls

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

# ------------------------------------------------------------------
BASE_DIR     = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
# ------------------------------------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="static")

@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")

# --------------- conversation state ----------------
dialog: deque[str]              = deque(maxlen=15)        # last 15 utterances
history_rgb: defaultdict[str,list] = defaultdict(list)    # last 5 RGB per user
clients: set[WebSocket]         = set()

# ---------------- helper: fan-out ------------------
async def broadcast(payload: dict, exclude: WebSocket | None = None):
    dead = set()
    for ws in clients:
        if ws is exclude:
            continue
        try:
            await ws.send_text(json.dumps(payload))
        except WebSocketDisconnect:
            dead.add(ws)
    for d in dead:
        clients.discard(d)

# ---------------- websocket ------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            msg = await ws.receive_json()

            # ---------- 1. WebRTC signalling relay ----------
            if "signal" in msg:
                await broadcast({"kind": "signal", "data": msg["signal"]}, exclude=ws)
                continue

            # ---------- 2. STT / emotion handling ----------
            user  = msg["user"]
            words = msg["words"]                      # list[ [word, ts] ]
            utts  = split_utterances(words)           # → [{"text": "..."}]

            for u in utts:
                dialog.append(f"#{user}#: {u['text']}")
                emo = emotion_cls(u["text"])         # e.g. "sad" / "sadness"
                history_rgb[user].append(rgb_for(emo))
                history_rgb[user] = history_rgb[user][-5:]

            summary = summarizer("\n".join(dialog))
            colours = {
                who: [int(x) for x in average_rgb(rgb_list)]
                for who, rgb_list in history_rgb.items()
            }

            await broadcast({"kind": "ui", "summary": summary, "colours": colours})

    finally:
        clients.discard(ws)

# ---------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)