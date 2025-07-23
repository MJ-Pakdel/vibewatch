import json
import re
from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage

import retriever
from prompting import PROMPT_TEMPLATE


class VibeWatchRecommender:
    """Simple wrapper around retriever + LLM generator."""

    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=temperature)

    def recommend(self, user_query: str, k: int = 5) -> List[Dict[str, str]]:
        docs = retriever.retrieve(user_query, k=k)

        prompt = PROMPT_TEMPLATE.format_prompt(user_query=user_query, retrieved_docs=json.dumps(docs, ensure_ascii=False))
        messages: List[BaseMessage] = prompt.to_messages()
        response = self.llm(messages)

        # Debug: print the raw response
        print(f"Raw LLM response: {response.content}")

        # Try to extract JSON from the response
        content = response.content.strip()
        
        # Look for JSON array in the response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                recs = json.loads(json_str)
                if isinstance(recs, list):
                    return recs
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
        
        # Try parsing the entire content as JSON
        try:
            recs = json.loads(content)
            if isinstance(recs, list):
                return recs
        except json.JSONDecodeError as e:
            print(f"Full content JSON parsing error: {e}")

        # Fallback: pass-through with docs
        return [
            {"title": m.get("title", ""), "reason": "(LLM parsing failed)"} for m in docs[:3]
        ] 