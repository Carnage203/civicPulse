# agents.py

import json
import re
from gemini_utils import get_gemini_model

# ✅ Initialize the Gemini model once (Singleton pattern will ensure single instance)
model = get_gemini_model()

def analyze_complaint(payload: dict):
    """
    Analyzes a resident complaint using the Gemini 2.5 Flash model.
    Returns structured JSON containing classification and insights.
    """

    # Prepare the input content
    contents = f"""
    Resident Name: {payload.get("resident_name")}
    Block/Area: {payload.get("block")}
    Description: {payload.get("description")}
    """

    try:
        # 🔹 Generate AI response using already initialized model
        response = model.generate_content(contents=contents)
        text_response = response.text.strip()

        # 🔹 Extract valid JSON if wrapped in markdown or text
        cleaned_text = re.search(r"\{.*\}", text_response, re.DOTALL)
        if cleaned_text:
            text_response = cleaned_text.group(0)

        # 🔹 Try parsing JSON safely
        try:
            ai_output = json.loads(text_response)
        except json.JSONDecodeError:
            ai_output = {"raw_text": text_response, "error": "Invalid JSON output"}

        # 🔹 Merge the AI output with original data
        final_output = {
            **payload,
            **ai_output,
            "status": "open"
        }

        return final_output

    except Exception as e:
        return {"error": str(e)}
