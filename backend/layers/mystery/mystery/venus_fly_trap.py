from abc import ABC
from typing import Callable

class Fly(Exception, ABC):
    '''Base class for exceptions that should be caught by VenusFlyTrap.'''
    def __init__(self, message: str) -> None:
        super().__init__(message)

class VenusFlyTrap:
    @ classmethod
    def catch_flies(cls, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Fly as fly:
                print(f'VenusFlyTrap caught a fly: {fly}')
                return None
        return wrapper