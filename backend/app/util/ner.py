import os
from typing import List

from spacy import Language, load
from spacy.tokens import Span


class NER:
    nlp: Language = None
    
    def __init__(self):
        if not self.nlp:
            print(os.listdir())
            print(os.listdir('../'))
            self.nlp = load('en_core_web_sm')
    
    def get_entities(self, text: str) -> List[Span]:
        if not text:
            return None

        doc = self.nlp(text)
        return doc.ents