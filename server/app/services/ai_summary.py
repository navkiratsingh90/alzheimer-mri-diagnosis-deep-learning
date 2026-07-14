import time
import random
import logging
from app.core.config import settings

# google.generativeai is fully deprecated and Google has already shut down
# ALL Gemini 1.0/1.5 models on it (returns 404 for every request now).
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

# Auto-updating alias — avoids re-breaking every time Google retires a
# dated model name (this app has already hit dead gemini-1.5-flash and
# gemini-2.5-flash model IDs).
GEMINI_MODEL = "gemini-flash-latest"

_client = None
if settings.GEMINI_API_KEY:
    _client = genai.Client(api_key=settings.GEMINI_API_KEY)


def _extract_retry_delay(error) -> float | None:
    """Pull the server-suggested retry delay (seconds) out of a 429 error, if present."""
    try:
        details = getattr(error, "details", None) or {}
        for item in details.get("error", {}).get("details", []):
            if "retryDelay" in item:
                return float(str(item["retryDelay"]).rstrip("s"))
    except Exception:
        pass
    return None


# Canonical stage names used for tip/context lookups. Real model output has
# been observed as "Moderate Dementia" while this dict originally only
# matched "Moderate Demented" — silently falling back to generic text for
# every non-exact match. This normalizes variants so lookups always hit.
def _normalize_stage(stage: str) -> str:
    s = (stage or "").lower()
    if "non" in s:
        return "Non Demented"
    if "very mild" in s or "verymild" in s:
        return "Very Mild Demented"
    if "moderate" in s:
        return "Moderate Demented"
    if "mild" in s:
        return "Mild Demented"
    return stage  # unrecognized — leave as-is, falls through to generic tip


def generate_ai_summary(predictions: list, max_retries: int = 3) -> str:
    """Generate a ~7-line clinical summary using Gemini."""
    if not _client:
        logger.warning("Gemini API key missing – using fallback.")
        return _get_fallback_summary(predictions)

    stages = [p['result'] for p in predictions]
    confidences = [p['confidence'] for p in predictions]

    prompt = (
        f"You are a clinical AI assistant. Based on these MRI predictions: {stages} "
        f"(confidence: {confidences}), write a 7-line summary covering:\n"
        "- overall assessment of the patient's condition\n"
        "- what the confidence level means\n"
        "- implications for daily life/cognition\n"
        "- recommended initial precautions\n"
        "- prognosis / need for specialist care\n"
        "Write in plain English, empathetic but factual."
    )

    # NOTE: the previous version made a separate "quick test" call before the
    # real one, silently doubling API usage on every summary generated —
    # significant on a 5-requests/minute free tier. Removed; we just attempt
    # the real call directly and fall back cleanly if it fails.
    last_error = None
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
            logger.error("Gemini returned an empty response – using fallback.")
            return _get_fallback_summary(predictions)

        except genai_errors.ClientError as e:
            last_error = e
            if getattr(e, "code", None) == 429 and attempt < max_retries - 1:
                retry_delay = _extract_retry_delay(e) or (2 ** attempt + random.uniform(0, 1))
                logger.warning(f"Gemini rate limited, retrying in {retry_delay:.1f}s...")
                time.sleep(retry_delay)
                continue
            logger.error(f"Gemini error: {e}")
            return _get_fallback_summary(predictions)

    logger.error(f"Gemini failed after {max_retries} retries: {last_error}")
    return _get_fallback_summary(predictions)


def _get_fallback_summary(predictions: list) -> str:
    """Short fallback summary based on the most common stage."""
    if not predictions:
        return "No predictions available."

    stages = [p['result'] for p in predictions]
    most_common_raw = max(set(stages), key=stages.count)
    most_common = _normalize_stage(most_common_raw)
    confidence = max(p['confidence'] for p in predictions)
    conf_pct = f"{confidence*100:.1f}%"

    stage_tips = {
        "Non Demented": "No strong Alzheimer's indicators. Maintain healthy habits and regular check-ups.",
        "Very Mild Demented": "Very early subtle changes. Establish a neurologist baseline and track symptoms.",
        "Mild Demented": "Mild cognitive impairment. Consult a neurologist, simplify routines, involve caregivers.",
        "Moderate Demented": "Moderate decline. Immediate specialist care, home safety, and caregiver support advised.",
    }
    tip = stage_tips.get(most_common, "Specialist consultation recommended.")

    # Display the ORIGINAL label from the model (e.g. "Moderate Dementia"),
    # not the normalized internal key, so the summary matches what's shown
    # elsewhere in the report.
    return (f"The analysis indicates {most_common_raw} with {conf_pct} confidence. {tip} "
            "Confidence is not diagnostic certainty - clinical correlation is essential. "
            "Regular follow-ups and lifestyle modifications are advised.")