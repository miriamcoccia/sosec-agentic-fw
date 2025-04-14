import os
import re
import pandas as pd
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
            print(f"⚠️ Warning: Unexpected model output '{v}'. Marking as 'invalid' for manual review.")
            return "invalid"
        return v


class TopicCheckerAgent:
    """
    An agent that classifies social media posts based on a given topic.

    Attributes:
        model (str): The LLM model to use for classification.
        keywords (list): A list of keywords strongly associated with the topic.
        topic (str): The topic the agent is checking for in the posts.
    """

    def __init__(self, model="llama3.2:latest", keywords=None, topic="a given topic"):
        """
        Initializes the classification agent.

        Args:
            model (str, optional): The LLM model to use. Defaults to "llama3.2:latest".
            keywords (list, optional): A list of keywords indicating topic relevance.
            topic (str, optional): The topic to classify posts about.
        """
        if keywords is None:
            keywords = []
        self.model = model
        self.keywords = keywords
        self.topic = topic

    def construct_message(self, user_message):
        """
        Constructs a prompt for the LLM to classify a post.

        Args:
            user_message (str): The social media post to classify.

        Returns:
            list: A list of dictionaries representing the structured message for the LLM.
        """
        return [
            {"role": "system", "content": (
                f"You are a highly accurate text classifier specializing in detecting references to {self.topic} "
                "in German-language social media posts, particularly on Telegram. "
                "Base your classification strictly on the content of the post, avoiding assumptions beyond what is explicitly stated."
            )},
            {"role": "user", "content": (
                "Classify the following Telegram post strictly based on its content:\n\n"
                f"Label it with '1' if the post references {self.topic} or any of its more specific aspects.\n"
                "Label it with '0' if it is about a different topic.\n"
                "If the classification is unclear, respond ONLY with 'Uncertain'.\n\n"
                f"Consider the following keywords as strong indicators that the post is about {self.topic}:\n"
                f"{', '.join(self.keywords)}\n\n"
                "However, do not rely solely on keywords—evaluate the full context of the message.\n\n"
                f"Post:\n{user_message}"
            )}
        ]

    def classify(self, user_message):
        """
        Sends the post to the LLM for classification.

        Args:
            user_message (str): The social media post to classify.

        Returns:
            str: The raw response from the LLM.
        """
        messages = self.construct_message(user_message)
        response = ollama.chat(model=self.model, messages=messages)
        return response["message"]["content"]

    def parse_output(self, response):
        """
        Parses the model's output to extract a valid classification label.

        Args:
            response (str): The LLM's response.

        Returns:
            str: The classification label ("0", "1", "Uncertain") or "invalid" if unrecognized.
        """
        response = response.strip()
        if re.search(r"uncertain", response, flags=re.IGNORECASE):
            return "Uncertain"
        match = re.search(r"\b[01]\b", response)
        return match.group() if match else "invalid"

    def process_dataset(self, inpath, outpath, checkpoint_path=None):
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
            print(f"Processing post: {post}")
            response = self.classify(post)
            raw_label = self.parse_output(response)
            validated_label = ClassificationOutput(label=raw_label).label  # Ensures valid output

            print(f"Model response: {response} → Recognized as {validated_label}")

            parsed_labels.append(validated_label)
            processed_texts.append(post)

            if (n + 1) % 10 == 0 and checkpoint_path:
                checkpoint_df = pd.DataFrame({"Post Text": processed_texts, "Label": parsed_labels})
                checkpoint_df.to_csv(checkpoint_path, mode="a", index=False, header=not os.path.exists(checkpoint_path))

        data_origin["Classification"] = parsed_labels
        data_origin.to_csv(outpath, index=False)
        print("Data saved successfully")


