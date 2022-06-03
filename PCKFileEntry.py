from dataclasses import dataclass

@dataclass
class PCKFileEntry:
    size: int
    type_: int
    name: str