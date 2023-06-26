from typing import Any, Dict, List, Literal, Set, get_args

from dstruct.model import (Block, Entity, StructuredProperty,
                           UnstructuredProperty)
from external.openai_ import OpenAI

IdentifiableKey = Literal['id', 'email', 'phone', 'address', 'url', 'username']

class EntityExtractor:
    _possible_identifiables: Set[IdentifiableKey] = set(list(get_args(IdentifiableKey)))

    def __init__(self, llm: OpenAI):
        self._llm = llm

    def with_defined_entities(self, dictionary: Dict[str, Any], entities: List[Entity]) -> None:
        print(f'[EntityExtractor.with_defined_entities] starting with dictionary length: {len(dictionary)} and entities length: {len(entities)}')
        dictionary_keys = dictionary.keys()
        print(f'[EntityExtractor.with_defined_entities] dictionary_keys: {dictionary_keys}')
        print(f'[EntityExtractor.with_defined_entities] possible_identifiables: {self._possible_identifiables}')
        if not self._possible_identifiables.isdisjoint(dictionary_keys) and 'name' in dictionary_keys:
            identifiables = set()
            for key in self._possible_identifiables:
                value = dictionary.get(key, None)
                if value:
                    identifiables.add(value)
            entities.append(Entity(identifiables=identifiables, name=dictionary.get('name')))

        for key, value in dictionary.items():
            print(f'[EntityExtractor.with_defined_entities] key: {key}, value: {value}, type {type(value)}')
            if isinstance(value, dict):
                self.with_defined_entities(value, entities)
                continue
            if key.endswith('_id'):
                entities.append(Entity(identifiables=set([value]), name=None))
        
        print(f'[EntityExtractor.with_defined_entities] ending with entities length: {len(entities)}')

    def _llm_find_entities(self, text: str) -> List[Entity]:
        print(f'[EntityExtractor._llm_find_entities] starting with text length: {len(text)}')

        # TODO: fix this prompt and give some few shot examples
        response = self._llm.function_call(
            messages=[{
                'role': 'system',
                'content': (
                    'You are NER-GPT. Given any text, you can extract entities from it. '
                    'An entity is a person or organization\'s name like an account, a company, a deal, etc. that is mentioned in the text. '
                    'For example, if I give you the text "John Smith lives in New York", '
                    'you can extract the entities "John Smith" and "New York". '
                    'You can also extract and associate those entities with identifiables if appropriate. '
                    'For example, if "John Smith" has a unique ID of "123" or a username of "jsmith" '
                    'or an email of "john_smith@gmail.com", you can associate those with "John Smith". '
                    'Names only! Ignore long meaningless strings, addresses, and numbers!'
                ),                
            }, {
                'role': 'user',
                'content': text,
            }],
            functions=[{
                'name': 'find_and_infer_entities',
                'description': 'Find and infer entities from the provided text.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'inferred_entities': {
                            'title': 'Inferred Entities',
                            'type': 'array',
                            'description': 'Entities without identifiables that can be interpreted from the text. This must be a name of a person or thing!!',
                            'items': {
                                'type': 'string'
                            },
                        },
                        'identifiable_entities': {
                            'title': 'Identifiable Entities',
                            'type': 'array',
                            'description': 'Entities that can be linked to an id, email, phone, address, etc.',
                            'items': {
                                'title': 'Identifiable Entity',
                                'type': 'object',
                                'properties': {
                                    'name': {
                                        'title': 'Name',
                                        'type': 'string',
                                        'description': 'The name of the entity.',
                                    },
                                    'identifiable_type': {
                                        'title': 'Identifiable Type',
                                        'type': 'string',
                                        'enum': list(self._possible_identifiables),
                                        'description': 'The type of identifiable.',
                                    },
                                    'identifiable': {
                                        'title': 'Identifiable',
                                        'type': 'string',
                                        'description': 'The actual identifiable itself associated with the type. For example, if the type is "id", then the identifiable is the actual ID "id-1234"',
                                    }
                                },
                                'required': ['name', 'identifiable_type', 'identifiable']
                            }
                        }
                    }
                }
            }],
            function_call={'name': 'find_and_infer_entities'},
            model='gpt-3.5-turbo-0613'
        )
        print(f'[EntityExtractor._llm_find_entities] response: {response}')
        entities: List[Entity] = []
        inferred_entities = response.get('inferred_entities', None)
        identifiable_entities = response.get('identifiable_entities', None)
        if inferred_entities:
            for inferred_entity_name in inferred_entities:
                entities.append(Entity(identifiables=None, name=inferred_entity_name))
        if identifiable_entities:
            for identifiable_entity in identifiable_entities:
                name = identifiable_entity.get('name')
                identifiable_type = identifiable_entity.get('identifiable_type')
                if identifiable_type not in self._possible_identifiables:
                    continue

                identifiable = identifiable_entity.get('identifiable')
                if name and identifiable_type and identifiable:
                    entities.append(Entity(identifiables=set([identifiable]), name=name))
        print(f'[EntityExtractor._llm_find_entities] ending with {len(entities)} entities')
        return entities

    # TODO: experiment with spaCy NER and see if it's better than LLM
    def with_llm_reasoned_entities(self, block: Block, entities: List[Entity]) -> None:
        print(f'[EntityExtractor.with_llm_reasoned_entities] starting with block length: {len(block.properties)} and entities length: {len(entities)}')

        aggregated_text = ''
        for property in block.properties:
            if isinstance(property, UnstructuredProperty):
                aggregated_text += '; '.join([chunk.text for chunk in sorted(property.chunks, key=lambda c: c.order)])
                for chunk in property.chunks:
                    aggregated_text += f'{chunk.text}'
            elif isinstance(property, StructuredProperty):
                aggregated_text += f'{property.value}'
            aggregated_text += '\n'

            if len(aggregated_text) > 6000:
                reasoned_entities = self._llm_find_entities(aggregated_text)
                entities.extend(reasoned_entities)
                aggregated_text = ''
        
        if aggregated_text:
            reasoned_entities = self._llm_find_entities(aggregated_text)
            entities.extend(reasoned_entities)

        print(f'[EntityExtractor.with_llm_reasoned_entities] ending with entities length: {len(entities)}')

    def deduplicate(self, entities: List[Entity]) -> None:
        deduplicated_entities: List[Entity] = []
        dictionary: Dict[str, Entity] = {}
        for entity in entities:
            dictionary_entity = None
            if entity.identifiables:
                for key in entity.identifiables:
                    dictionary_entity = dictionary.get(key, None)
                    if dictionary_entity:
                        break  
            if not dictionary_entity and entity.name:
                dictionary_entity = dictionary.get(entity.name, None)

            if not dictionary_entity:
                deduplicated_entities.append(entity)
                if entity.identifiables:
                    for key in entity.identifiables:
                        dictionary[key] = entity
                if entity.name:
                    dictionary[entity.name] = entity
            else:
                dictionary_entity.name = entity.name if len(entity.name) > len(dictionary_entity.name) else dictionary_entity.name
                if not dictionary_entity.identifiables:
                    dictionary_entity.identifiables = entity.identifiables
                elif entity.identifiables:
                    dictionary_entity.identifiables.update(entity.identifiables)

        entities.clear()
        entities.extend(deduplicated_entities)
