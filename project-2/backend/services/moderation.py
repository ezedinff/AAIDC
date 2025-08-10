import os
from config import get_config
from openai import OpenAI


def _llm_moderation_flagged(text: str) -> bool:
    """Use OpenAI moderation to flag unsafe content. Safe fallback on error."""
    try:
        cfg = get_config()
        if not cfg.get("openai_api_key"):
            return False
        client = OpenAI(api_key=cfg["openai_api_key"])
        resp = client.moderations.create(model="omni-moderation-latest", input=text)
        result = resp.results[0]
        min_score = float(os.getenv("MODERATION_MIN_SCORE", "0.08"))
        scores = getattr(result, "category_scores", None)
        if scores:
            max_score = max(getattr(scores, k) for k in scores.__dict__.keys() if not k.startswith("_"))
            if max_score >= min_score:
                return True
        return bool(getattr(result, "flagged", False))
    except Exception:
        return False 