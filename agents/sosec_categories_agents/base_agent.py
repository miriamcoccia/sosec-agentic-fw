import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator

class ClassificationOutput(BaseModel):
    """
    A Pydantic model for validating classification outputs.

    Attributes:
        label (str): The classification label, which should be "0", "1", or "Uncertain".
    """
    label: str

    @field_validator("label", mode="before")
    @classmethod
    def validate_label(cls, v):
        """
        Ensures that the label is one of the expected values.

        Args:
            v (str): The label output from the model.

        Returns:
            str: The validated label. If invalid, returns "invalid" and logs a warning.
        """
        valid_labels = {"0", "1", "Uncertain"}
        if v not in valid_labels:
            logging.warning(f"Unexpected model output '{v}'. Marking as 'invalid' for manual review.")
            return "invalid"
        return v

class BaseClassificationAgent:
    def __init__(self, model: str, category_name: str, category_descriptions: dict):
        self.model = model
        self.category_name = category_name
        self.category_details = category_descriptions.get(category_name, {})

    def generate_response(self, messages):
        try:
            response = ollama.chat(model=self.model, messages=messages)
            return response["message"]["content"].strip()
        except Exception as e:
            logging.error(f"Error during LLM call: {e}")
            return "Error occurred during LLM call"

    def construct_messages(self, post_text: str):
        system_message = (
            f"You are an expert text classification assistant. Your task is to determine whether the following Telegram post falls into the category of '{self.category_name}'. "
            "This category includes posts that discuss, for example, the following aspects:\n"
        )
        for subcategory, description in self.category_details.items():
            system_message += f"- {subcategory}: {description}\n"

        user_message = (
            "Classify the following Telegram post strictly based on its content:\n\n"
            f"Label it with '1' if the post references {self.category_name} or any of its more specific aspects.\n"
            "Label it with '0' if it is about a different topic.\n"
            "If the classification is unclear, respond ONLY with 'Uncertain'.\n\n"
            f"Post:\n'{post_text}'"
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def classify_post(self, post_text: str) -> str:
        messages = self.construct_messages(post_text)
        response = self.generate_response(messages)
        response = response.upper().strip()
        validated_label = ClassificationOutput(label=response).label
        return validated_label

    def process_dataset(self, inpath: str, outpath: str, checkpoint_path: str = None):
        """
        Processes a dataset of posts, classifying each one and saving the results.

        Args:
            inpath (str): Path to the input CSV file containing the posts.
            outpath (str): Path to save the output CSV file with classifications.
            checkpoint_path (str, optional): Path to a checkpoint CSV file to resume interrupted processing.

        Returns:
            None: Saves the classified dataset to a CSV file.
        """
        parsed_labels = []
        processed_texts = []

        if checkpoint_path and os.path.exists(checkpoint_path):
            data = pd.read_csv(checkpoint_path)
            raw_messages = data["Post Text"].tolist()
        else:
            data_origin = pd.read_csv(inpath)
            raw_messages = data_origin["Post Text"].tolist()

        for n, post in enumerate(raw_messages):
            logging.info(f"Processing post: {post}")
            response = self.classify_post(post)
            logging.info(f"Model response: {response}")
            parsed_labels.append(response)
            processed_texts.append(post)

            if (n + 1) % 10 == 0 and checkpoint_path:
                checkpoint_df = pd.DataFrame({"Post Text": processed_texts, self.category_name.lower().replace(" ", "_"): parsed_labels})
                checkpoint_df.to_csv(checkpoint_path, mode="a", index=False, header=not os.path.exists(checkpoint_path))

        data_origin[self.category_name] = parsed_labels
        data_origin.to_csv(outpath, index=False)
        logging.info("Data saved successfully")

# Example usage
# class ViewGermanyUsaAgent(BaseClassificationAgent):
#     def __init__(self, model: str):
#         super().__init__(model, "General Concerns", CATEGORY_DESCRIPTIONS)

# if __name__ == "__main__":
#     classifier = ViewGermanyUsaAgent(MODEL)
#     post = "The media is lying to us all, they control the entire #narrative!"
#     result = classifier.classify_post(post)
#     print(f"Classification: {result}")
