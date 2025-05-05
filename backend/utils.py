# utils.py  – emotion colours + helpers
from __future__ import annotations
from typing import Tuple, Dict, List

# canonical palette
EMO_RGB: Dict[str, Tuple[int, int, int]] = {
    "neutral":  (128, 128, 128),
    "joy":      (255, 215,   0),
    "surprise": (  0, 255, 255),
    "anger":    (255,   0,   0),
    "sadness":  (  0,   0, 139),
    "disgust":  (  0, 128,   0),
    "fear":     (128,   0, 128),
}

# aliases that OpenAI sometimes returns when we force 1-token answers
ALIAS = {
    "sad": "sadness",
    "dis": "disgust",
    "ang": "anger",
    "sur": "surprise",
    "neu": "neutral",
}

def rgb_for(label: str) -> Tuple[int, int, int]:
    """Return an RGB triple for *any* variant of the seven emotions."""
    key = ALIAS.get(label.lower(), label.lower())
    return EMO_RGB.get(key, EMO_RGB["neutral"])

# ---------------- average helper (unchanged) ----------------
def average_rgb(colours: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
    if not colours:
        return (128, 128, 128)
    r = sum(c[0] for c in colours) // len(colours)
    g = sum(c[1] for c in colours) // len(colours)
    b = sum(c[2] for c in colours) // len(colours)
    return (r, g, b)