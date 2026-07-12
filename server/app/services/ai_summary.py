import google.generativeai as genai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def generate_ai_summary(predictions: list) -> str:
    """
    Generate a clinical summary using Gemini.
    Returns a ~7-8 line narrative with assessment, confidence, implications, and initial steps.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("Gemini API key missing – using fallback summary.")
        return _get_fallback_summary(predictions)

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Try multiple model names in order of preference (gemini-2.5-pro is widely available)
    model_names = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-pro"]
    model = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # Quick test to validate the model
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            break
        except Exception:
            continue
    if not model:
        logger.error("No Gemini model available – using fallback.")
        return _get_fallback_summary(predictions)

    stages = [p['result'] for p in predictions]
    confidences = [p['confidence'] for p in predictions]

    prompt = (
        "You are a clinical AI assistant specialised in Alzheimer's disease. "
        "Based on the following MRI classification predictions, write a 7–8 line professional summary. "
        "The summary must cover:\n"
        "1. An overall assessment of the patient's condition based on the stage.\n"
        "2. A clear explanation of what the confidence level means (how certain the model is).\n"
        "3. What this stage typically implies for daily life and cognition.\n"
        "4. Recommended initial precautions or lifestyle changes.\n"
        "5. What to expect going forward (prognosis / need for specialist care).\n\n"
        "Use empathetic yet factual language. Write in plain English, no bullet points or markdown.\n\n"
        f"Predictions (stages): {stages}\n"
        f"Confidence scores: {confidences}\n"
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return _get_fallback_summary(predictions)


def _get_fallback_summary(predictions: list) -> str:
    """Detailed fallback summary tailored to the most common stage."""
    if not predictions:
        return "No predictions available to generate summary."

    # Pick the most frequent result
    stages = [p['result'] for p in predictions]
    most_common = max(set(stages), key=stages.count)
    confidence = max(p['confidence'] for p in predictions)  # use highest confidence
    confidence_pct = f"{confidence*100:.1f}%"

    # Detailed stage descriptions (each ~3 lines)
    stage_descriptions = {
        "Non Demented": (
            "The MRI scan shows no strong indicators of Alzheimer's-related decline. "
            "This is a reassuring result, though it reflects a single point in time. "
            "Maintain a healthy lifestyle, stay mentally and socially active, and continue regular check‑ups. "
            "If any memory or behavioural changes arise, consult a neurologist promptly."
        ),
        "Very Mild Demented": (
            "The scan shows early, subtle patterns that may indicate the very earliest cognitive changes. "
            "At this stage, symptoms are often barely noticeable in daily life. "
            "It is advisable to establish a baseline with a neurologist, keep a symptom journal, "
            "and adopt brain‑healthy habits (exercise, diet, sleep) to support long‑term cognitive health."
        ),
        "Mild Demented": (
            "The scan shows patterns consistent with mild cognitive impairment. "
            "Memory lapses, difficulty with complex tasks, or occasional disorientation may become noticeable. "
            "Many individuals at this stage remain independent with appropriate support. "
            "Consult a neurologist for formal assessment, consider simplifying daily routines, "
            "and involve family or caregivers in care planning."
        ),
        "Moderate Demented": (
            "The scan shows more pronounced patterns consistent with moderate cognitive decline. "
            "Daily activities may require increasing support, and changes in memory, judgment, "
            "or behaviour are typically more noticeable. "
            "Immediate specialist consultation is recommended to develop a comprehensive care plan, "
            "including medication management, home safety adjustments, and caregiver support."
        ),
    }

    description = stage_descriptions.get(
        most_common,
        "The scan was analysed and classified. A specialist consultation is recommended for personalised advice."
    )

    return (
        f"The analysis indicates a {most_common} pattern with {confidence_pct} confidence. "
        f"{description} "
        f"Confidence level reflects how closely the scan matched the predicted category, " 
        "but it is not a diagnostic certainty – clinical correlation is essential. "
        "Regular follow‑ups and lifestyle modifications are advised."
    )