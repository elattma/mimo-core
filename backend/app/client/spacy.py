from dataclasses import dataclass
from typing import List

from spacy import Language, load
from spacy.tokens import Span


@dataclass
class TripletPart:
    text: str
    type: str

@dataclass
class Triplet:
    subject: TripletPart
    predicate: TripletPart
    object: TripletPart

class Spacy:
    nlp: Language = None
    
    def __init__(self):
        if not self.nlp:
            self.nlp = load('en_core_web_sm')
    
    def get_entities(self, text: str) -> List[Span]:
        if not text:
            return None

        doc = self.nlp(text)
        return doc.ents

    def get_triplets(self, text: str) -> List[Triplet]:
        return []
        # if not text:
        #     return None
        # 
        # doc = self.nlp(text)
        # triplets: List[Triplet] = []
        # for chunk in doc.noun_chunks:
        #     if chunk.root.dep_ == 'ROOT':
        #         subject = None
        #         predicate = None
        #         object = None
        #         for child in chunk.root.children:
        #             if child.dep_ == 'nsubj':
        #                 subject = child.text
        #             elif child.dep_ == 'dobj':
        #                 object = child.text
        #         if subject and object:
        #             triplets.append(Triplet(
        #                 subject=subject,
        #                 predicate=chunk.root.text,
        #                 object=object
        #             ))
        # return triplets