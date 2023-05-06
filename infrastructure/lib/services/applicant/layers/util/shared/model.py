from dataclasses import dataclass


@dataclass
class App:
    id: str = None
    name: str = None
    created_at: int = None
    
    def is_valid(self):
        return self.id and self.name and self.created_at
    