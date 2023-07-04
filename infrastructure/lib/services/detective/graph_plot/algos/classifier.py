from logging import getLogger
from typing import Any, Dict

from lake.label_config import LABEL_NORMALIZE_MAP
from store.block_state import (MESSAGE_BLOCK_LABEL, MESSAGE_THREAD_BLOCK_LABEL,
                               SUPPORTED_BLOCK_LABELS)

_logger = getLogger('Classifier')

class Classifier:
    def __init__(self, log_level: int) -> None:
        _logger.setLevel(log_level)

    def get_normalized_label(self, label: str) -> str:
        if not label:
            _logger.exception(f'[get_normalized_label] empty label!')

        if label in LABEL_NORMALIZE_MAP:
            return LABEL_NORMALIZE_MAP.get(label)

        for supported_label in SUPPORTED_BLOCK_LABELS:
            if supported_label in label:
                return supported_label
        
        _logger.info(f'[get_normalized_label] invalid label: {label}')
        return None
    
    def _is_valid_id(self, id: Any) -> bool:
        if not id:
            return False
        
        if isinstance(id, str):
            return True
        
        return False
    
    def _pop_and_validate(self, raw_dict: Dict, key: str) -> Any:
        value = raw_dict.pop(key, None)
        if self._is_valid_id(value):
            return value
        
        return None

    def find_id(self, raw_dict: Dict, label: str = None) -> str:
        if not raw_dict:
            return None
        
        id = self._pop_and_validate(raw_dict=raw_dict, key="id")
        if id:
            return id
        
        # TODO: add other validations
        # TODO: fuzzy match on other fields if applicable, maybe make this configurable
        if label:
            if label == MESSAGE_THREAD_BLOCK_LABEL:
                id = self._pop_and_validate(raw_dict=raw_dict, key="thread_ts")
                if id:
                    return id
            if label == MESSAGE_BLOCK_LABEL:
                id = self._pop_and_validate(raw_dict=raw_dict, key="ts")
                if id:
                    return id
            
        return None