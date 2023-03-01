from dataclasses import dataclass


@dataclass
class Integration:
    id: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    oauth2_link: str = ""
    authorized: bool = False