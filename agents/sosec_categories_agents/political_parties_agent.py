import os
import re
import pandas as pd
import logging
import ollama
from pydantic import BaseModel, field_validator
from base_agent import BaseClassificationAgent


CATEGORY_DESCRIPTIONS = {"Political Parties and Opinions": {
    "Party Preferences": "Opinions on the approval or disapproval of certain parties.",
    "Party Ideologies and Political Positions": "Posts about the ideologies of parties and their positions on the political spectrum.",
    "Voting Intentions": "Expressions of voting intentions, either for or against certain parties.",
    "Evaluation of Political Positions": "Opinions on political positions and the alignment of parties with one's own beliefs."
}}

class PoliticalPartiesAgent(BaseClassificationAgent):
    def __init__(self, model: str):
         super().__init__(model, "Political Parties and Opinions", CATEGORY_DESCRIPTIONS)
