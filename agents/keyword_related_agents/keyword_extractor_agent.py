import pandas as pd
import ollama
import re
from pydantic import BaseModel, field_validator
from collections import defaultdict

class KeywordExtractionOutput(BaseModel):
    """
    Pydantic model to validate and ensure the Llama-extracted keywords are formatted correctly.
    """
    keywords: list[str]

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, v):
        """
        Ensures the extracted keywords are a valid list of strings.
        :param v: Raw extracted keywords.
        """
        if not isinstance(v, list) or not all(isinstance(word, str) for word in v):
            raise ValueError("Invalid keyword format. Expected a list of strings.")
        return v

class KeywordExtractorAgent:
    """
    AI Agent that analyzes categorized text data and extracts representative keywords
    using Llama (Ollama).
    """

    def __init__(self, model="llama3.2:latest", num_keywords=10):
        """
        Initializes the agent.

        :param model: Name of the Llama model to use.
        :param num_keywords: Number of top keywords to extract per category.
        """
        self.model = model
        self.num_keywords = num_keywords

    def construct_prompt(self, category, texts, texts_others):
        """
        Constructs the prompt for Llama to extract characteristic keywords for a category.

        :param category: The category label.
        :param texts: List of texts belonging to this category.
        :param texts_others: List of texts belonging to the categories that are not the provided category label.
        :return: Formatted system + user prompt.
        """
        joined_texts = "\n".join(texts)
        joined_texts_others = "\n".join(texts_others)

        return [
            {"role": "system", "content": (
                f"You are an expert in keyword extraction in German-language social media who can identify the most relevant keyword that specify a particular text or collection of texts. "
                f"Your task is to analyze a collection of social media posts (Telegram) and determine the most characteristic keywords that define the topic '{category}'."
            )},
            {"role": "user", "content": (
                f"Extract exactly {self.num_keywords} keywords or key phrases that best represent the category. Focus on meaningful terms that differentiate this category from others.\n\n"
                f"Here are some sample posts from the '{category}' category:\n{joined_texts}\n\n"
                f"Here are some sample posts from the other categories: \n{joined_texts_others[:20]}"
                "Provide only a comma-separated list of keywords."
            )}
        ]

    def extract_keywords(self, category, texts):
        """
        Uses Llama to extract the most relevant keywords for a given category.

        :param category: The category label.
        :param texts: List of texts belonging to this category.
        :return: List of extracted keywords.
        """
        prompt = self.construct_prompt(category, texts, texts_others)
        try:
            response = ollama.chat(model=self.model, messages=prompt)
            raw_output = response.get("message", {}).get("content", "")
            extracted_keywords = self.parse_output(raw_output)
        except Exception as e:
            print(f"Error extracting keywords for category '{category}': {e}")
            return []
    
        return KeywordExtractionOutput(keywords=extracted_keywords).keywords

    def parse_output(self, response):
        """
        Parses Llama's response and extracts keywords.

        :param response: Raw response from Llama.
        :return: List of extracted keywords.
        """
        response = response.strip()
        keywords = re.split(r",\s*", response)

        return [kw.strip() for kw in keywords if kw]

    def process_dataset(self, filepath, category_col="Category", text_col="Post Text"):
        """
        Processes a dataset and extracts keywords for each category.
    
        :param filepath: Path to the dataset (CSV format).
        :param category_col: Column name for categories.
        :param text_col: Column name for the text content.
        :return: Dictionary mapping each category to its extracted keywords.
        """
        data = pd.read_csv(filepath)
        categories = data[category_col].unique()
        category_keywords = {}
    
        for category in categories:
            category_texts = data[data[category_col] == category][text_col].tolist()
            texts_others = data[data[category_col] != category][text_col].tolist()
    
            if not category_texts:
                category_keywords[category] = []
                continue
    
            try:
                keywords = self.extract_keywords(category, category_texts, texts_others)
                category_keywords[category] = keywords
            except Exception as e:
                print(f"Error extracting keywords for category '{category}': {e}")
                category_keywords[category] = []
    
        return category_keywords
    def save_keywords_to_csv(self, category_keywords, filepath="keywords_by_category.csv"):
        """
        Saves the extracted keywords to a CSV file using Pandas.
    
        :param category_keywords: Dictionary mapping categories to keywords.
        :param filepath: Path to save the CSV file.
        """
        # Convert the dictionary into a Pandas DataFrame
        df = pd.DataFrame([
            {"Category": category, "Keywords": ", ".join(keywords)}
            for category, keywords in category_keywords.items()
        ])
        
        # Save the DataFrame to a CSV file
        df.to_csv(filepath, index=False, encoding="utf-8")
        print(f"Keywords successfully saved to {filepath}")



# Example Usage
# agent = KeywordExtractorAgent()
# keywords_by_category = agent.process_dataset("categorized_posts.csv")
# print(keywords_by_category)
