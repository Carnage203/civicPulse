# gemini_utils.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_gemini_model():
    """
    Returns a configured Gemini 2.5 Flash model with CivicPulse system instruction.
    """
    system_instruction = """
    You are an AI assistant for a smart civic complaint management system called "CivicPulse".
    Your task is to analyze resident complaints and output a structured JSON with these fields:
    - category: choose one from ["Water Supply", "Cleanliness", "Electricity", "Road Maintenance",
                                 "Garbage Management", "Noise Pollution", "Public Safety",
                                 "Street Lighting", "Drainage", "Other"]
    - sentiment: (positive, negative, neutral)
    - severity_level: (low, medium, high)
    - urgency_score: (integer 0–10)
    - llm_summary: (a short one-line summary)
    - action_recommendation: (a short, practical suggestion for authorities)

    Return ONLY a valid JSON object — no explanations or markdown.
    Example:
    {
        "category": "Electricity",
        "sentiment": "negative",
        "severity_level": "high",
        "urgency_score": 8,
        "llm_summary": "Power outage reported in Block B for last 2 hours",
        "action_recommendation": "Send maintenance team to inspect the transformer"
    }
    """

    # Initialize the model with system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )
    return model
