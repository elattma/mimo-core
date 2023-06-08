from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from mystery.query import (Concepts, Integration, IntegrationsFilter, Query,
                           QueryComponent, ReturnType, ReturnTypeValue,
                           SearchMethod, SearchMethodValue)


class Override(ABC):
    @abstractmethod
    def apply_to_query(self, query: Query):
        raise Exception('Override.apply_to_query() not implemented.')

@dataclass
class PageOverride(Override):
    integration: str
    page_id: str

    def apply_to_query(self, query: Query):
        to_delete: List[QueryComponent] = []
        for key in query.components.keys():
            if key is IntegrationsFilter:
                query.components[key] = IntegrationsFilter(
                    integrations=[self.integration],
                    page_ids=[self.page_id]
                )
            elif key is SearchMethod:
                query.components[key] = SearchMethod(
                    value=SearchMethodValue.RELEVANT
                )
            elif key is Concepts:
                continue
            else:
                to_delete.append(key)
        for key in to_delete:
            del query.components[key]
        query.components[SearchMethod] = SearchMethod(
            value=SearchMethodValue.RELEVANT
        )
        query.components[ReturnType] = ReturnType(
            value=ReturnTypeValue.BLOCKS
        ) 
    
    @property
    def integration_enum(self):
        if self.integration == 'google_docs':
            return Integration.DOCUMENTS
        elif self.integration == 'google_mail':
            return Integration.EMAIL
        elif self.integration == 'zoho':
            return Integration.CRM
        elif self.integration == 'zendesk':
            return Integration.CUSTOMER_SUPPORT