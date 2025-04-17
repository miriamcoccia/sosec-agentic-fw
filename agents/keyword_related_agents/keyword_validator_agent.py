import ollama
from typing import List, Optional
from pydantic import BaseModel, field_validator
import logging

class KeywordVerificationOutput(BaseModel):
    """
    Pydantic model for the keyword verification output.
    """
    original_keywords: List[str]
    suggested_keywords: Optional[List[str]]
    final_keywords: List[str]
    verification_passed: bool

    @field_validator("original_keywords", mode="before")
    @classmethod
    def validate_original_keywords(cls, v):
        if not isinstance(v, list) or not all(isinstance(kw, str) for kw in v):
            raise ValueError("original_keywords must be a list of strings.")
        return v

    @field_validator("suggested_keywords", mode="before")
    @classmethod
    def validate_suggested_keywords(cls, v):
        if v is None:
            return v
        if not isinstance(v, list) or not all(isinstance(kw, str) for kw in v):
            raise ValueError("suggested_keywords must be a list of strings.")
        return v

    @field_validator("final_keywords", mode="before")
    @classmethod
    def validate_final_keywords(cls, v):
        if not isinstance(v, list) or not all(isinstance(kw, str) for kw in v):
            raise ValueError("final_keywords must be a list of strings.")
        return v


class KeywordVerifierAgent:
    """
    Verifies and possibly expands keyword sets using LLM.
    Preserves subtle data-derived terms while optionally adding broader, generalizable terms.
    """

    def __init__(self, model: str = "llama3.2:latest"):
        self.model = model

    def construct_prompt(self, category: str, keywords: List[str], sample_texts: List[str]) -> List[dict]:
        joined_texts = "\n".join(sample_texts)
        joined_keywords = ", ".join(keywords)

        return [
            {
                "role": "system",
                "content": (
                    "You are a keyword evaluation assistant. You receive real keywords extracted from social media posts "
                    "for a category. Preserve these original keywords. Only suggest new keywords if absolutely necessary. "
                    "Output should be:\n- 'PASS' if the original keywords are sufficient\n"
                    "- OR a comma-separated list of additional keywords ONLY (no explanations)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Category: {category}\n\n"
                    f"Sample Posts:\n{joined_texts}\n\n"
                    f"Original Keywords: {joined_keywords}\n\n"
                    "Your response must be only 'PASS' or a list like this: keyword1, keyword2, keyword3"
                )
            }
        ]

    def verify_keywords(self, category: str, original_keywords: List[str], sample_texts: List[str]) -> KeywordVerificationOutput:
        prompt = self.construct_prompt(category, original_keywords, sample_texts)
        try:
            response = ollama.chat(model=self.model, messages=prompt)
            raw_output = response.get("message", {}).get("content", "").strip()

            if raw_output.upper().startswith("PASS"):
                return KeywordVerificationOutput(
                    original_keywords=original_keywords,
                    suggested_keywords=None,
                    final_keywords=original_keywords,
                    verification_passed=True
                )

            # Handle LLM-suggested keywords (clean & deduplicated)
            suggested_keywords = [
                kw.strip().strip('"').strip("'") for kw in raw_output.split(",") if kw.strip()
            ]
            final_keywords = sorted(set(original_keywords + suggested_keywords))

            return KeywordVerificationOutput(
                original_keywords=original_keywords,
                suggested_keywords=suggested_keywords,
                final_keywords=final_keywords,
                verification_passed=False
            )

        except Exception as e:
            logging.error(f"Keyword verification failed for '{category}': {e}")
            return KeywordVerificationOutput(
                original_keywords=original_keywords,
                suggested_keywords=None,
                final_keywords=original_keywords,
                verification_passed=False
            )


# === 🔍 Testing the Agent ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    original_keywords = ["debate", "election", "policy"]
    sample_texts = [
        "The recent debate on climate policy has sparked discussions about the future of coastal cities.",
        "In the upcoming election, candidates are focusing on environmental policies.",
        "Political leaders are clashing over the new economic reform plans."
    ]

    logging.info("Initializing KeywordVerifierAgent...")
    verifier = KeywordVerifierAgent()

    logging.info("Verifying keywords...")
    result = verifier.verify_keywords("Politics", original_keywords, sample_texts)

    print("\n✅ Final Output:")
    print("Original Keywords     :", result.original_keywords)
    print("Suggested Keywords    :", result.suggested_keywords if result.suggested_keywords else "None")
    print("Final Keywords to Use :", result.final_keywords)
    print("Verification Passed   :", result.verification_passed)
