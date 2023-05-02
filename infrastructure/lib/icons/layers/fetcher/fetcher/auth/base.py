from abc import ABC, abstractmethod
from typing import Any


class Auth(ABC):
    _TYPE = 'base'

    subclasses = {}

    @classmethod
    def create(cls, type: str, **kwargs) -> Any:
        if not cls.subclasses:
            cls.subclasses = {subclass._TYPE: subclass for subclass in cls.__subclasses__()}

        if not type or not cls.subclasses.get(type, None):
            raise NotImplementedError(f'auth not found for {type}')
        
        return cls.subclasses[type](**kwargs)

    @abstractmethod
    def authorize(self, params: dict) -> bool:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass