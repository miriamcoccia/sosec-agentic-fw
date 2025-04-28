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
    Data model for structuring the output from GTrendsAgent.

    Attributes:
        original_keywords (List[str]): List of original keywords provided as input.
        suggested_keywords (List[str]): List of suggested keywords obtained from Google Trends.
        related_keywords (List[str]): List of related keywords obtained from related queries.
        all_keywords (List[str]): Consolidated and cleaned list of all collected keywords.
    """

    original_keywords: List[str]
    suggested_keywords: List[str]
    related_keywords: List[str]
    all_keywords: List[str]

    @field_validator("original_keywords", "suggested_keywords", "related_keywords", "all_keywords", mode="before")
    @classmethod
    def validate_keywords(cls, v):
        """
        Validator to ensure each field is a list of strings.

        Args:
            v: The value to validate.

        Raises:
            ValueError: If the value is not a list of strings.
        """
        if not isinstance(v, list) or not all(isinstance(kw, str) for kw in v):
            raise ValueError("Each keyword list must be a list of strings.")
        return v


class GTrendsAgent:
    """
    Agent class to interact with Google Trends and collect suggested and related keywords.

    Methods:
        clean_keyword(kw): Checks if a keyword is valid based on length and printability.
        get_suggestions(use_mid): Fetches keyword suggestions based on original keywords.
        get_related_keywords(): Fetches related queries for all known keywords.
        get_all_keywords(): Aggregates and deduplicates all collected keywords.
        run(): Executes the full keyword retrieval pipeline and returns validated output.
    """

    def __init__(self, original_keywords: Optional[List[str]] = None):
        """
        Initialize GTrendsAgent with optional original keywords.

        Args:
            original_keywords (Optional[List[str]]): List of keywords to initialize with.
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
        """
        Validate that a keyword is a printable string with reasonable length.

        Args:
            kw (str): Keyword to validate.

        Returns:
            bool: True if keyword is valid, False otherwise.
        """
        return isinstance(kw, str) and 1 < len(kw) < 50 and kw.isprintable()

    def get_suggestions(self, use_mid: bool = False) -> List[str]:
        """
        Retrieve keyword suggestions from Google Trends.

        Args:
            use_mid (bool): Whether to use Google's 'mid' identifier instead of titles.

        Returns:
            List[str]: List of unique, cleaned suggested keywords.
        """
        all_suggestions = []

        for keyword in self.original_keywords:
            try:
                suggestions = self.pytrend.suggestions(keyword=keyword)
                if suggestions:
                    entries = [s['mid'] if use_mid else s['title'] for s in suggestions]
                    all_suggestions.extend(filter(self.clean_keyword, entries))
            except Exception as e:
                logging.warning(f"⚠️ Failed to get suggestions for '{keyword}': {e}")
            time.sleep(random.uniform(10, 15))  # Random delay to reduce risk of being rate-limited

        self.sugg_keywords = list(set(all_suggestions))
        return self.sugg_keywords

    def get_related_keywords(self) -> List[str]:
        """
        Retrieve related queries based on original and suggested keywords.

        Returns:
            List[str]: List of unique, cleaned related keywords.
        """
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

            time.sleep(random.uniform(10, 15))  # Respectful sleep to avoid banning

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
        """
        Consolidate and deduplicate all keywords collected.

        Returns:
            List[str]: List of all validated keywords.
        """
        self.total_keywords = list(set(
            filter(self.clean_keyword,
                   self.original_keywords + self.sugg_keywords + self.related_keywords)))
        return self.total_keywords

    def run(self) -> GTrendsOutput:
        """
        Execute the full keyword gathering process.

        Returns:
            GTrendsOutput: Structured output containing all keyword lists.
        """
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
    # Configure logging settings
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

    # Example usage
    test_keywords = ['Erdbeeren']  # Change keywords to avoid temporary bans (429 errors)
    agent = GTrendsAgent(original_keywords=test_keywords)

    try:
        output = agent.run()
        print("✅ GTrendsAgent successfully ran!\n")
        pprint.pprint(output.model_dump())
    except Exception as e:
        logging.error("❌ Error occurred while running GTrendsAgent:", exc_info=e)
