from logging import getLogger
from typing import Any, Dict

from lake.label_config import LABEL_NORMALIZE_MAP
from store.block_state import SUPPORTED_BLOCK_LABELS

_logger = getLogger('Classifier')

class Classifier:
    def __init__(self, log_level: int) -> None:
        _logger.setLevel(log_level)

    def get_normalized_label(self, label: str):
        if not label:
            raise Exception(f'[S3Lake.get_normalized_label] invalid label: {label}')

        if label in LABEL_NORMALIZE_MAP:
            return LABEL_NORMALIZE_MAP.get(label)

        for supported_label in SUPPORTED_BLOCK_LABELS:
            if supported_label in label:
                return supported_label
        
        raise Exception(f'[Normalizer.get_normalized_label] invalid label: {label}')
    
    def _is_valid_id(self, id: Any) -> bool:
        if not id:
            return False
        
        if isinstance(id, str):
            return True
        
        return False

    def find_id(self, raw_dict: Dict) -> str:
        if not raw_dict:
            return None
        
        id = raw_dict.pop("id", None)
        # TODO: add other validations
        # TODO: fuzzy match on other fields if applicable, maybe make this configurable
        if self._is_valid_id(id):
            return id
        
        return None