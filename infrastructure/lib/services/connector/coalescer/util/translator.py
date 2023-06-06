from typing import Dict, List

from dstruct.model import Block


# TODO: make more sophisticated
class Translator:
    def __init__(self, label_property_prefix: Dict[str, Dict[str, str]] = {}) -> None:
        self._label_property_prefix = label_property_prefix

    def translate(self, chunked_block: List[Block]) -> str:
        accumulator: List[str] = []
        for block in chunked_block:
            translated = None
            if block.label in self._label_property_prefix:
                property_prefix = self._label_property_prefix[block.label]
                translated = self.translate_block(block, property_prefix)
            else:
                translated = f'For data labeled {block.label}. '
                translated += f'Properties include: {block.properties} ' if block.properties else ''
                translated += f'Unstructed text: {block.unstructured}' if block.unstructured else ''
            accumulator.append(translated)
        return '\n\n'.join(accumulator)

    @staticmethod
    def translate_block(block: Block, property_prefix: Dict[str, str]) -> str:
        translated = f'For data labeled {block.label}. '
        for name, value in block.properties.items():
            if name in property_prefix:
                translated += f'{property_prefix[name]} {value}. '
            else:
                translated += f'{name} is {value}. '
        if block.unstructured:
            translated += f'Text: {block.unstructured}'
    