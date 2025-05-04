from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn, asyncio, json, logging
from collections import deque, defaultdict
from utils import EMO_RGB, average_rgb
from segmentation import split_utterances
from models import summarizer, emotion_cls

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

# ------------------------------------------------------------------
# resolve absolute path to ../frontend  (works from any cwd)
BASE_DIR      = Path(__file__).resolve().parent.parent   # project root
FRONTEND_DIR  = BASE_DIR / "frontend"
# ------------------------------------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# serve all static files under /static/…
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR), html=False),
    name="static"
)

# serve index.html at /
@app.get("/")
async def get_index():
    return FileResponse(FRONTEND_DIR / "index.html")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

# rolling buffers
dialog     : deque[str]             = deque(maxlen=15)   # 15 utterances across both users
history_rgb: defaultdict[str,list]  = defaultdict(list)  # per-user last 5 RGB

clients: set[WebSocket] = set()

async def broadcast(payload: dict):
    dead = set()
    for ws in clients:
        try:    await ws.send_text(json.dumps(payload))
        except WebSocketDisconnect:
            dead.add(ws)
    for d in dead: clients.discard(d)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            msg = await ws.receive_json()   # {"user":"A","words":[["hello",0.1], ...]}
            user  = msg["user"]
            words = msg["words"]            # stream chunk already timestamped
            utts  = split_utterances(words)
            logging.debug(f"[Utterance dataset] {utts!r}")
            for u in utts:
                dialog.append(f"#{user}#: {u['text']}")
                logging.debug(f"[Dialog dataset] appended → {list(dialog)}")
                emo   = emotion_cls(u["text"])
                logging.debug(f"[Emotion output] “{u['text']}” → {emo}")
                history_rgb[user].append(EMO_RGB[emo])
                history_rgb[user] = history_rgb[user][-5:]   # keep last 5
                logging.debug(f"[Emotion history] last-5 RGB for {user}: {history_rgb[user]}")
            # prepare UI update
            summary = summarizer("\n".join(dialog))
            logging.debug(f"[Summary output] {summary!r}")
            colours = {
                user: [int(v) for v in average_rgb(rgb_list)]
                for user, rgb_list in history_rgb.items()
            }
            logging.debug(f"[Emotion average] {colours}")
            await broadcast({"summary": summary, "colours": colours})
    finally:
        clients.discard(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)