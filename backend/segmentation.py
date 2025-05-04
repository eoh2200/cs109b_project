def split_utterances(words: list[tuple[str,float]]) -> list[dict]:
    """
    Args
        words : list of (word, timestamp_seconds) sorted by time
    Returns
        list of dicts {text, ts_start, ts_end}
    """
    utterances, current, start = [], [], None
    for w, t in words:
        if start is None:                       # first word
            start = t
        if current and (t - current[-1][1]) > 1.0:  # >1 s gap → new utterance
            utterances.append({
                "text": " ".join(w for w,_ in current),
                "ts_start": start,
                "ts_end":  current[-1][1]})
            current, start = [], None
        current.append((w,t))
    # flush last
    if current:
        utterances.append({
            "text": " ".join(w for w,_ in current),
            "ts_start": start,
            "ts_end":  current[-1][1]})
    return utterances