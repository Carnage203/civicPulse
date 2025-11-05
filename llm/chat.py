import re
from llm.llm_client import gemini_client
from llm.prompts import CHATBOT_PROMPT
from mongodb.mongo_client import complaints_collection
from typing import List
from google.genai import types


client = gemini_client.client

def chatbot(query: str):
    
    block = re.search(r'\bblock\s*([A-Z]\d*)\b', query, re.IGNORECASE)
    block = block.group(1).upper() if block else None

    query_vector = embed_generator(query)
    vector_results = vector_search_complaints(query_vector, block)
    contents = (
        "CONTEXT:\n"
        + "\n".join(
            f"- {doc.get('resident_name')} ({doc.get('block')}): "
            f"{doc.get('description').strip()}"
            for doc in vector_results
        )
        + f"\n\nUSER_QUERY:\n{query.strip()}"
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
            system_instruction=CHATBOT_PROMPT),
            contents=contents)
        text_response = response.text.strip()
        cleaned_text = re.search(r"\{.*\}", text_response, re.DOTALL)
        if cleaned_text:
            text_response = cleaned_text.group(0)
    except Exception as e:
        return {"error": str(e)}
    return text_response

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

def vector_search_complaints(query_vector: List[float], block: str = None):
    if not query_vector or not isinstance(query_vector, list):
        raise ValueError("query_vector must be a non-empty list of floats.")

    filters = [
        {"status": {"$in": ["open", "pending"]}}
    ]

    if block:
        block = block.upper().strip()

        if re.match(r"^[A-Z]\d+$", block):
            filters.append({"block": {"$eq": block}})

        elif re.match(r"^[A-Z]$", block):
            possible_blocks = [f"{block}{i}" for i in range(1, 10)]  
            filters.append({"block": {"$in": possible_blocks}})
    
    vector_filters = {"$and": filters}

    pipeline = [
    {
        "$vectorSearch": {
            "index": "complaints_embedding_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": 300,
            "limit": 20,
            "filter": vector_filters
        }
    },
    {
        "$project": {
            "_id": 0,
            "resident_name": 1,
            "description": 1,
            "block": 1,
            "score": {"$meta": "vectorSearchScore"}
        }
    }
    ]

    results = complaints_collection.aggregate(pipeline)
    return list(results)
