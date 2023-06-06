from dataclasses import dataclass


@dataclass
class CoalescerArgs:
    connection: str
    library: str

    def valid(self) -> bool:
        return all([
            self.connection,
            self.library,
        ])