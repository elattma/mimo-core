from typing import Any, Dict, List

from dstruct.model import Block, Entity


class EntityExtractor:
    def find_entities(self, dictionary: Dict[str, Any]) -> List[Entity]:
        # TODO: implement by grabbing entities from structured fields
        pass

    def find_inferrable_entities(self, block: Block) -> List[str]:
        # TODO: experiment with an llm call or spaCy call to extract potential entities from unstructured fields
        return []
