import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from llm.prompts import ANALYZE_COMPLAINT_PROMPT

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

        embedding = embed_generator(payload.get("description"))
        final_output = {
            **payload,
            **ai_output,
            "embedding": embedding,
            "status": "open"
        }

        return final_output

    except Exception as e:
        return {"error": str(e)}
        

def embed_generator(contents:str):
    try:
        response = client.models.embed_content(
        model="gemini-embedding-001",
        contents= contents
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None

