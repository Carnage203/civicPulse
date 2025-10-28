import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts import ANALYZE_COMPLAINT_PROMPT

load_dotenv()

client = genai.Client()

def analyze_complaint(payload: dict):
    """
    Analyzes a resident complaint using the Gemini 2.5 Flash model.
    Returns structured JSON containing classification and insights.
    """

    contents = f"""
    Resident Name: {payload.get("resident_name")}
    Block/Area: {payload.get("block")}
    Description: {payload.get("description")}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
            system_instruction=ANALYZE_COMPLAINT_PROMPT),
            contents=contents)
        text_response = response.text.strip()

        cleaned_text = re.search(r"\{.*\}", text_response, re.DOTALL)
        if cleaned_text:
            text_response = cleaned_text.group(0)

        try:
            ai_output = json.loads(text_response)
        except json.JSONDecodeError:
            ai_output = {"raw_text": text_response, "error": "Invalid JSON output"}

        final_output = {
            **payload,
            **ai_output,
            "status": "open"
        }

        return final_output

    except Exception as e:
        return {"error": str(e)}
    
if __name__ == "__main__":
    payload = {
        "resident_name": "Ritika Sharma",
        "block": "Sector 8",
        "description": "Street lights have not been working for the past 3 nights and the area feels unsafe."
    }

    result = analyze_complaint(payload)
    print(json.dumps(result, indent=4))
