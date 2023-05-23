from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

class Type(Enum):
    INT = 0
    STRING = 1
    BOOL = 2
    NULL = 3
    OBJ = 4

@dataclass
class Method:
    name: str
    return_type: Tuple[Type, str | None]
    parameters: List[Tuple[Type, str, str]]     # param type, param name, param obj name (optional)
    body: any

@dataclass
class Field:
    name: str
    type: Type
    value: any
    obj_name: str = None