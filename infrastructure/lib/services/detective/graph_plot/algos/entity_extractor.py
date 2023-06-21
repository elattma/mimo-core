from typing import Dict, List

from dstruct.model import Block, Entity


class EntityExtractor:
    def find_entities(self, raw_dict: Dict) -> List[Entity]:
        # Grab entities from structured fields
        pass

    def find_inferrable_entities(self, block: Block) -> List[str]:
        # TODO: experiment with an llm call or spaCy call to extract potential entities from unstructured fields
        return []
