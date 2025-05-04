import os
from dotenv import load_dotenv
from openai import OpenAI

# ─── Load API key from .env and instantiate client ──────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarizer(dialog: str, max_words: int = 25) -> str:
    """
    Returns a summary of `dialog` in no more than `max_words` words.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",   # or "gpt-4o" if available
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that generates extremely concise conversation "
                    f"summaries in no more than {max_words} words."
                )
            },
            {
                "role": "user",
                "content": f"Summarize this dialogue in ≤{max_words} words:\n\n{dialog}"
            }
        ],
        temperature=0.3,
        max_tokens=max_words * 2  # safe upper bound
    )
    return resp.choices[0].message.content.strip()

def emotion_cls(text: str) -> str:
    """
    Classifies `text` into exactly one of:
    neutral, joy, surprise, anger, sadness, disgust, fear.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that classifies text into exactly one of: "
                    "neutral, joy, surprise, anger, sadness, disgust, fear."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Utterance: “{text}”\n\n"
                    "Which single emotion does it convey? Reply with only the one-word label."
                )
            }
        ],
        temperature=0.0,
        max_tokens=1
    )
    return resp.choices[0].message.content.strip().lower()