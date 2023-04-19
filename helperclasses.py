from dataclasses import dataclass
from typing import List

@dataclass
class Method:
    name: str
    parameters: List[str]
    body: any

@dataclass
class Field:
    name: str
    value: any