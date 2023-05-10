from dataclasses import dataclass
from enum import Enum
from typing import List

@dataclass
class Method:
    name: str
    parameters: List[str]
    body: any

class Type(Enum):
    INT = 0
    STRING = 1
    BOOL = 2
    NULL = 3
    OBJ = 4

@dataclass
class Field:
    name: str
    type: Type
    value: any