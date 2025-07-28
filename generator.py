import json
import re
from typing import List, Dict

# Third-party
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage

# Standard library
import logging

# Local imports
import retriever
from prompting import PROMPT_TEMPLATE

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


class VibeWatchRecommender:
    """Simple wrapper around retriever + LLM generator."""

    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=temperature)

    def recommend(self, user_query: str, k: int = 5) -> List[Dict[str, str]]:
        docs = retriever.retrieve(user_query, k=k)

        prompt = PROMPT_TEMPLATE.format_prompt(user_query=user_query, retrieved_docs=json.dumps(docs, ensure_ascii=False))
        messages: List[BaseMessage] = prompt.to_messages()
        response = self.llm(messages)

        # Debug: log the raw response
        logger.debug("Raw LLM response: %s", response.content)
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
                logger.debug("JSON parsing error: %s", e)
        
        # Try parsing the entire content as JSON
        try:
            recs = json.loads(content)
            if isinstance(recs, list):
                # Enrich LLM recommendations with poster URLs from original docs
                return self._enrich_with_posters(recs, docs)
        except json.JSONDecodeError as e:
            logger.debug("Full content JSON parsing error: %s", e)

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
        
        # Debug: log available titles and their poster status
        logger.debug("Available titles and posters:")
        for title, poster in title_to_poster.items():
            poster_status = "✓ HAS POSTER" if poster else "✗ NO POSTER"
            logger.debug("  '%s' -> %s", title, poster_status)
            if poster:
                logger.debug("    URL: %s", poster)
        
        logger.debug("LLM recommended titles:")
        # Add poster URLs to recommendations
        for rec in recs:
            title = rec.get("title", "")
            logger.debug("  Looking for: '%s'", title)
            
            # Initialize poster as None to ensure the key always exists
            rec["poster"] = None
            
            if title in title_to_poster:
                rec["poster"] = title_to_poster[title]
                logger.debug("    ✓ MATCHED -> %s", title_to_poster[title])
            else:
                logger.debug("    ✗ NO MATCH FOUND")
                # Try fuzzy matching
                for doc_title in title_to_poster:
                    # Safely compare by casting to string to avoid errors if title is not str
                    title_str = str(title).lower()
                    doc_title_str = str(doc_title).lower()
                    if title_str in doc_title_str or doc_title_str in title_str:
                        rec["poster"] = title_to_poster[doc_title]
                        logger.debug("    ~ FUZZY MATCH: '%s' -> '%s' -> %s", title, doc_title, title_to_poster[doc_title])
                        break
                
                # If still no poster found, keep it as None (but key exists)
                if rec["poster"] is None:
                    logger.debug("    ✗ NO POSTER AVAILABLE - will use placeholder")
        
        return recs 