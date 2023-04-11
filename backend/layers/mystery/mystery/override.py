from abc import ABC, abstractmethod
from dataclasses import dataclass

from mystery.query import IntegrationsFilter, Query


class Override(ABC):
    @abstractmethod
    def apply_to_query(self, query: Query):
        raise Exception('Override.apply_to_query() not implemented.')

@dataclass
class PageOverride(Override):
    integration: str
    page_id: str

    def apply_to_query(self, query: Query):
        if IntegrationsFilter not in query.components:
            query.components[IntegrationsFilter] = IntegrationsFilter(
                integrations=[self.integration],
                page_ids=[self.page_id]
            )
            return
        
        integrations_filter: IntegrationsFilter = query.components[IntegrationsFilter]
        if not integrations_filter.integrations:
            integrations_filter.integrations = [self.integration]
        elif self.integration not in integrations_filter.integrations:
            integrations_filter.integrations.append(self.integration)
        
        if not integrations_filter.page_ids:
            integrations_filter.page_ids = [self.page_id]
        elif self.page_id not in integrations_filter.page_ids:
            integrations_filter.page_ids.append(self.page_id)
    