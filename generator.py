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
                    # Enrich LLM recommendations with poster URLs from original docs
                    return self._enrich_with_posters(recs, docs)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
        
        # Try parsing the entire content as JSON
        try:
            recs = json.loads(content)
            if isinstance(recs, list):
                # Enrich LLM recommendations with poster URLs from original docs
                return self._enrich_with_posters(recs, docs)
        except json.JSONDecodeError as e:
            print(f"Full content JSON parsing error: {e}")

        # Fallback: pass-through with docs (preserve all metadata including poster)
        return [
            {
                "title": m.get("title", ""), 
                "reason": "(LLM parsing failed)",
                "poster": m.get("poster")  # Preserve poster URL
            } for m in docs[:3]
        ]
    
    def _enrich_with_posters(self, recs: List[Dict], docs: List[Dict]) -> List[Dict]:
        """Enrich LLM recommendations with poster URLs by matching titles"""
        # Create a lookup map from title to poster URL
        title_to_poster = {doc.get("title", ""): doc.get("poster") for doc in docs}
        
        # Debug: print available titles and their poster status
        print("DEBUG: Available titles and posters:")
        for title, poster in title_to_poster.items():
            poster_status = "✓ HAS POSTER" if poster else "✗ NO POSTER"
            print(f"  '{title}' -> {poster_status}")
            if poster:
                print(f"    URL: {poster}")
        
        print("DEBUG: LLM recommended titles:")
        # Add poster URLs to recommendations
        for rec in recs:
            title = rec.get("title", "")
            print(f"  Looking for: '{title}'")
            
            # Initialize poster as None to ensure the key always exists
            rec["poster"] = None
            
            if title in title_to_poster:
                rec["poster"] = title_to_poster[title]
                print(f"    ✓ MATCHED -> {title_to_poster[title]}")
            else:
                print(f"    ✗ NO MATCH FOUND")
                # Try fuzzy matching
                for doc_title in title_to_poster:
                    if title.lower() in doc_title.lower() or doc_title.lower() in title.lower():
                        rec["poster"] = title_to_poster[doc_title]
                        print(f"    ~ FUZZY MATCH: '{title}' -> '{doc_title}' -> {title_to_poster[doc_title]}")
                        break
                
                # If still no poster found, keep it as None (but key exists)
                if rec["poster"] is None:
                    print(f"    ✗ NO POSTER AVAILABLE - will use placeholder")
        
        return recs 