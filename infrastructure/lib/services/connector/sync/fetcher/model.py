from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List


class PageType(Enum):
    CRM = 'crm'
    DOCS = 'docs'
    MAIL = 'mail'
    CUSTOMER_SUPPORT = 'customer_support'
    MESSAGING = 'messaging'

class SectionType(Enum):
    PERSON = 'person'
    ACCESS = 'access'
    UNSTRUCTURED_TEXT = 'unstructured_text'
    CHAINED_TEXT = 'chained_text'
    DEAL = 'deal'
    CONTACT_INFO = 'contact_info'

@dataclass
class Filter:
    start_timestamp: int = None
    limit: int = 20

@dataclass
class Section(ABC):
    created_at: int
    updated_at: int
    
    @classmethod
    @abstractmethod
    def get_type(cls) -> SectionType:
        raise NotImplementedError
    
@dataclass
class PersonSection(Section):
    id: str
    name: str
    email: str = None

    @classmethod
    def get_type(cls) -> SectionType:
        return SectionType.PERSON
    
@dataclass
class AccessSection(Section):
    pass

@dataclass
class UnstructuredTextSection(Section):

    text: str
    id_author: str

    @classmethod
    def get_type(cls) -> SectionType:
        return SectionType.UNSTRUCTURED_TEXT

@dataclass
class ChainedTextSection(Section):
    text: str
    id_author: str
    id_previous: str

    @classmethod
    def get_type(cls) -> SectionType:
        return SectionType.CHAINED_TEXT
    
@dataclass
class DealSection(Section):
    name: str
    id_owner: str
    id_contacts: List[str]
    type: str
    stage: str
    close_date: str
    amount: int
    probability: int

    @classmethod
    def get_type(cls) -> SectionType:
        return SectionType.DEAL

@dataclass
class ContactInfoSection(Section):
    id_person: str
    id_owner: str
    department: str
    title: str
    lead_source: str

    @classmethod
    def get_type(cls) -> SectionType:
        return SectionType.DEAL

@dataclass
class Page:
    id: str
    type: PageType