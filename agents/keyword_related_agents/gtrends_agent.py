import requests
import time
import random
import logging
import pprint
from pytrends.request import TrendReq
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator


class GTrendsOutput(BaseModel):
    """
    Pydantic model to validate and structure the output from GTrendsAgent.
    """
    original_keywords: List[str]
    suggested_keywords: List[str]
    related_keywords: List[str]
    all_keywords: List[str]

    @field_validator("original_keywords", "suggested_keywords", "related_keywords", "all_keywords", mode="before")
    @classmethod
    def validate_keywords(cls, v):
        if not isinstance(v, list) or not all(isinstance(kw, str) for kw in v):
            raise ValueError("Each keyword list must be a list of strings.")
        return v


class GTrendsAgent:
    """
    An agent that interacts with the Google Trends API to retrieve suggested and related search keywords 
    based on a set of original keywords.
    """

    def __init__(self, original_keywords: Optional[List[str]] = None):
        """
        Initialize the agent with an optional list of original keywords.
        Uses German language and region context.
        """
        self.pytrend = TrendReq(
            hl='de-DE',
            tz=360,
            timeout=(10, 25),
            retries=2,
            backoff_factor=0.1,
            requests_args={
                "headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/123.0.0.0 Safari/537.36"
                    )
                }
            }
        )

        self.original_keywords = original_keywords if original_keywords else []
        self.sugg_keywords = []
        self.related_keywords = []
        self.total_keywords = []

    def clean_keyword(self, kw: str) -> bool:
        return isinstance(kw, str) and 1 < len(kw) < 50 and kw.isprintable()

    def get_suggestions(self, use_mid: bool = False) -> List[str]:
        all_suggestions = []
        for keyword in self.original_keywords:
            try:
                suggestions = self.pytrend.suggestions(keyword=keyword)
                if suggestions:
                    entries = [s['mid'] if use_mid else s['title'] for s in suggestions]
                    all_suggestions.extend(filter(self.clean_keyword, entries))
            except Exception as e:
                logging.warning(f"⚠️ Failed to get suggestions for '{keyword}': {e}")
            time.sleep(random.uniform(10, 15))  # Longer delay to avoid CAPTCHA
        self.sugg_keywords = list(set(all_suggestions))
        return self.sugg_keywords

    def get_related_keywords(self) -> List[str]:
        known_keywords = set(filter(self.clean_keyword, self.original_keywords + self.sugg_keywords))
        related_kws = []

        for kw in known_keywords:
            try:
                self.pytrend.build_payload([kw], geo='DE')
                related_queries = self.pytrend.related_queries()
                result = related_queries.get(kw, {})
            except Exception as e:
                logging.warning(f"⚠️ Failed to get related queries for '{kw}': {e}")
                continue
            time.sleep(random.uniform(10, 15))

            for kind in ['top', 'rising']:
                df = result.get(kind)
                if df is not None:
                    for rel_kw in df['query']:
                        if self.clean_keyword(rel_kw) and rel_kw not in known_keywords:
                            related_kws.append(rel_kw)
                            known_keywords.add(rel_kw)

        self.related_keywords = list(set(related_kws))
        return self.related_keywords

    def get_all_keywords(self) -> List[str]:
        self.total_keywords = list(set(
            filter(self.clean_keyword,
                   self.original_keywords + self.sugg_keywords + self.related_keywords)))
        return self.total_keywords

    def run(self) -> GTrendsOutput:
        logging.info("🤖 Running GTrendsAgent...")
        self.get_suggestions()
        logging.info(f"👀 Suggested Keywords: {self.sugg_keywords}")
        self.get_related_keywords()
        logging.info(f"🪼 Related Keywords: {self.related_keywords}")
        all_keywords = self.get_all_keywords()
        logging.info(f"🔑 All Keywords: {all_keywords}")
        return GTrendsOutput(
            original_keywords=self.original_keywords,
            suggested_keywords=self.sugg_keywords,
            related_keywords=self.related_keywords,
            all_keywords=all_keywords
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

    test_keywords = ['Erdbeeren']  # Use new keywords while recovering from 429 bans
    agent = GTrendsAgent(original_keywords=test_keywords)

    try:
        output = agent.run()
        print("✅ GTrendsAgent successfully ran!\n")
        pprint.pprint(output.model_dump())
    except Exception as e:
        logging.error("❌ Error occurred while running GTrendsAgent:", exc_info=e)
