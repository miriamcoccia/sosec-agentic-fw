import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator
from base_agent import BaseClassificationAgent

CATEGORY_DESCRIPTIONS = {"General Concerns": {
    "Financial Stability and Cost of Living": "Posts about concerns regarding bills, shopping restrictions, or financial security.",
    "Environmental and Climate Protection Concerns": "Posts about climate or environmental protection issues and pollution.",
    "Russia-Ukraine Conflict": "Posts about the impacts of the Ukraine war and geopolitical concerns.",
    "Refugee Situation": "Posts about the situation and impacts of Ukrainian and non-Ukrainian refugees in Germany.",
    "Health and Healthcare System": "Opinions and concerns about the availability and quality of the healthcare system.",
    "Societal Prosperity": "Thoughts on general prosperity and the future development of society."
}}

class GeneralConcernsAgent(BaseClassificationAgent):
    def __init__(self, model: str):
         super().__init__(model, "General Concerns", CATEGORY_DESCRIPTIONS)

