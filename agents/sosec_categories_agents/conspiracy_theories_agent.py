import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator
from base_agent import BaseClassificationAgent


CATEGORY_DESCRIPTIONS = {
    "Conspiracy Theories and Socio-Political Narratives": {
        "Belief in crises orchestrated by elites": "Posts suggesting that crises are deliberately engineered by elites.",
        "Distrust towards state and media narratives": "Content questioning the integrity or motives of mainstream reporting.",
        "Censorship and freedom of speech concerns": "Opinions on the suppression of views deemed 'inappropriate.'",
        "Surveillance and data privacy concerns": "Discussions about digital privacy, surveillance, and distrust in big tech or media companies.",
        "Claims of foreign influence": "Assertions that foreign entities manipulate national politics or governance."
    }
}


class ConspiracyTheoriesAgent(BaseClassificationAgent):
    def __init__(self, model: str):
         super().__init__(model, "Conspiracy Theories and Socio-Political Narratives", CATEGORY_DESCRIPTIONS)