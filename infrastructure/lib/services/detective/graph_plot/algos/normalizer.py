from typing import Any, Dict, Set

from dstruct.model import Property, StructuredProperty, UnstructuredProperty


# TODO: experiment with using LLMs to normalize text or determine whether a property is structured
class Normalizer:
    def _get_flattened(self, raw_dict: Dict[str, Any], accumulate_key: str = '') -> str:
        flattened = ''
        for key, value in raw_dict.items():
            if flattened:
                flattened += ', '

            if isinstance(value, dict):
                flattened += self._get_flattened(value, accumulate_key + key + '_')
            else:
                flattened += f'(key: {accumulate_key + key}, value: {value})'
        return flattened

    def _is_valid_value(self, value: Any) -> bool:
        if value is None:
            return False
        elif value == "":
            return False
        elif value == []:
            return False
        elif value == {}:
            return False
        elif value == "null":
            return False
        elif value == "None":
            return False
        elif value == "[]":
            return False
        elif value == "{}":
            return False
        elif value == " ":
            return False
        else:
            return True

    def _to_structured_property(self, key: str, value: Any) -> StructuredProperty:
        return StructuredProperty(key=key, value=value)
    
    def _to_unstructured_property(self, key: str, value: str) -> UnstructuredProperty:
        # TODO: chunk the string into multiple unstructured properties if it exceeds MAX_UNSTRUCTURED_SIZE
        return UnstructuredProperty(key=key, value=value)
    
    def _to_property(self, key: str, value: Any) -> Property:
        if isinstance(value, dict):
            flattened = self._get_flattened(value)
            return self._to_unstructured_property(key=key, value=flattened)

        if isinstance(value, (int, float)):
            return self._to_structured_property(key=key, value=value)
        
        # TODO: normalize any timestamp or datetime object format
        # TODO: unstructured string chunking etc.

    def sanitize(self, dictionary: Dict[str, Any]) -> None:
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.sanitize(value)
            if not self._is_valid_value(value):
                del dictionary[key]

    def to_properties(self, dictionary: Dict[str, Any]) -> Set[Property]:
        properties = set()
        for key, value in dictionary.items():
            property = self._to_property(key, value)
            if property:
                properties.add(property)

        return properties
    
    def find_last_updated_timestamp(self, dictionary: Dict[str, Any]) -> int:
        pass
