import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, List

EMO_RGB = {
    "neutral": (176, 176, 176),
    "joy":     (255, 215,   0),
    "surprise":(  0, 255, 255),
    "anger":   (211,  47,  47),
    "sadness": ( 30, 136, 229),
    "disgust": (107, 142,  35),
    "fear":    (138,  43, 226),
}

def average_rgb(rgb_list: List[Tuple[int,int,int]]) -> Tuple[int,int,int]:
    """Simple arithmetic mean of last N RGB tuples."""
    arr = np.array(rgb_list, dtype=np.float32)
    return tuple(arr.mean(axis=0).astype(int))