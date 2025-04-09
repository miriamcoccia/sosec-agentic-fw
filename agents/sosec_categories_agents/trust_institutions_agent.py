import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator
from base_agent import BaseClassificationAgent

CATEGORY_DESCRIPTIONS = {"Trust in Institutions": {
    "Government and Leadership": "Trust in political leadership and government transparency.",
    "Media and Press": "Trust in media, including traditional, online, and independent news sources.",
    "Military and Police": "Trust in institutions such as the military and police.",
    "Legal and Judicial System": "Trust in the legal system and judiciary, including administrative bodies.",
    "Public Health and Welfare Institutions": "Trust in the healthcare system and social welfare institutions."
}}

class TrustInstitutionsAgent(BaseClassificationAgent):
    def __init__(self, model: str):
         super().__init__(model, "Trust in Institutions", CATEGORY_DESCRIPTIONS)


