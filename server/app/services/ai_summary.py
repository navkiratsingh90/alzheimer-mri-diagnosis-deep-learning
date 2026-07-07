import openai
from app.core.config import settings

def generate_ai_summary(predictions: list) -> str:
    """
    Generate a clinical summary using OpenAI.
    predictions: list of dicts with keys 'result', 'confidence', 'timestamp'
    """
    if not settings.OPENAI_API_KEY:
        return "AI summary not available – please provide an API key."

    # Build context
    stages = [p['result'] for p in predictions]
    confidences = [p['confidence'] for p in predictions]
    prompt = (
        "You are a clinical AI assistant. Summarise the following Alzheimer's MRI predictions:\n"
        f"Predictions: {stages}\nConfidence scores: {confidences}\n"
        "Provide a brief, professional summary of the patient's progression and any recommendations."
    )

    openai.api_key = settings.OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"