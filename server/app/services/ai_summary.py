import google.generativeai as genai
from app.core.config import settings

def generate_ai_summary(predictions: list) -> str:
    """
    Generate a clinical summary using Gemini 2.5.
    predictions: list of dicts with keys 'result', 'confidence', 'timestamp'
    """
    if not settings.GEMINI_API_KEY:
        return "AI summary not available – please provide a Gemini API key."

    # Configure the client
    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Use the latest Gemini 2.5 model (Pro or Flash)
    model = genai.GenerativeModel("gemini-2.5-pro")  # or "gemini-2.5-flash"

    # Build a structured prompt for clinical context
    stages = [p['result'] for p in predictions]
    confidences = [p['confidence'] for p in predictions]
    prompt = (
        "You are a clinical AI assistant specialised in Alzheimer's disease. "
        "Based on the following MRI classification predictions, provide a concise, "
        "professional summary and actionable recommendations.\n\n"
        f"Predictions (stages): {stages}\n"
        f"Confidence scores: {confidences}\n\n"
        "Include:\n"
        "- An overall assessment of the patient's condition.\n"
        "- A note on the confidence levels.\n"
        "- Recommended next steps for the clinician.\n"
        "Keep the tone empathetic yet factual."
    )

    try:
        response = model.generate_content(prompt)
        # The response object has a .text attribute
        return response.text.strip()
    except Exception as e:
        # Fallback: log the error and return a basic summary
        print(f"Gemini API error: {e}")
        # Provide a simple summary based on the most frequent stage
        if predictions:
            most_common = max(set(stages), key=stages.count)
            return (f"Patient shows {most_common} pattern. "
                    f"Please consult a specialist. (AI summary generated fallback)")
        return "No predictions available to generate summary."