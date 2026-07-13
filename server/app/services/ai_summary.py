import google.generativeai as genai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def generate_ai_summary(predictions: list) -> str:
    """Generate a ~7‑line clinical summary using Gemini (single model)."""
    if not settings.GEMINI_API_KEY:
        logger.warning("Gemini API key missing – using fallback.")
        return _get_fallback_summary(predictions)

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Use a single reliable model
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Quick test
        model.generate_content("test", generation_config={"max_output_tokens": 1})
    except Exception:
        logger.error("Gemini model unavailable – using fallback.")
        return _get_fallback_summary(predictions) 

    stages = [p['result'] for p in predictions]
    confidences = [p['confidence'] for p in predictions]

    prompt = (
        f"You are a clinical AI assistant. Based on these MRI predictions: {stages} "
        f"(confidence: {confidences}), write a 7‑line summary covering:\n"
        "– overall assessment of the patient's condition\n"
        "– what the confidence level means\n"
        "– implications for daily life/cognition\n"
        "– recommended initial precautions\n"
        "– prognosis / need for specialist care\n"
        "Write in plain English, empathetic but factual."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return _get_fallback_summary(predictions)


def _get_fallback_summary(predictions: list) -> str:
    """Short fallback summary based on the most common stage."""
    if not predictions:
        return "No predictions available."

    stages = [p['result'] for p in predictions]
    most_common = max(set(stages), key=stages.count)
    confidence = max(p['confidence'] for p in predictions)
    conf_pct = f"{confidence*100:.1f}%"

    stage_tips = {
        "Non Demented": "No strong Alzheimer's indicators. Maintain healthy habits and regular check‑ups.",
        "Very Mild Demented": "Very early subtle changes. Establish a neurologist baseline and track symptoms.",
        "Mild Demented": "Mild cognitive impairment. Consult a neurologist, simplify routines, involve caregivers.",
        "Moderate Demented": "Moderate decline. Immediate specialist care, home safety, and caregiver support advised.",
    }
    tip = stage_tips.get(most_common, "Specialist consultation recommended.")

    return (f"The analysis indicates {most_common} with {conf_pct} confidence. {tip} "
            "Confidence is not diagnostic certainty – clinical correlation is essential. "
            "Regular follow‑ups and lifestyle modifications are advised.")