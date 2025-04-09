import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator
from base_agent import BaseClassificationAgent


CATEGORY_DESCRIPTIONS = {"View on Germany/USA": {
    "Political and Social Climate": "Posts about political topics, social stability, and general governance.",
    "Freedom of Speech": "Concerns regarding the ability to express opinions freely and without fear.",
    "Social Cohesion and Polarization": "Perception of unity or division within the country.",
    "Political Debates": "Opinions on the current tone and openness of political discussions.",
    "Migration Policy": "Views on migration policy, capacities, and cultural impacts of migration.",
    "Crisis Management Compared to Previous Years": "Thoughts on how the government handles crises compared to previous years."
}}

class ViewGermanyUsaAgent(BaseClassificationAgent):
    def __init__(self, model: str):
         super().__init__(model, "View on Germany/USA", CATEGORY_DESCRIPTIONS)

