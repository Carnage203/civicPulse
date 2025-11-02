import json
import os
from collections import defaultdict
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mongodb.handlers import get_all_complaints

load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def summarize_block_issues():
    """
    Fetch all complaints from MongoDB, group them block-wise,
    and summarize each block's issues using Gemini.
    """

    # Step 1: Fetch all complaints from DB
    complaints = get_all_complaints()
    if not complaints:
        print("⚠️ No complaints found in database.")
        return []

    # Step 2: Group complaints by block
    block_wise_complaints = defaultdict(list)
    for c in complaints:
        block = c.get("block", "Unknown")
        block_wise_complaints[block].append(c.get("description", ""))

    # Step 3: Summarize each block using Gemini
    block_summaries = []

    for block, descriptions in block_wise_complaints.items():
        all_text = "\n".join(descriptions)

        prompt = f"""
        You are an AI civic data analyst for the CivicPulse system.
        Summarize the main issues and recurring problems reported by residents
        in Block {block}. Be concise (2-3 sentences) and focus on key concerns.
        
        Complaints:
        {all_text}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="Summarize civic complaints clearly and briefly."
                ),
                contents=prompt
            )

            summary_text = response.text.strip()
            block_summaries.append({"block": block, "summary": summary_text})

        except Exception as e:
            print(f"⚠️ Error summarizing block {block}: {e}")
            block_summaries.append({"block": block, "summary": "Error generating summary."})

    return block_summaries


if __name__ == "__main__":
    summaries = summarize_block_issues()
    print(json.dumps(summaries, indent=4))