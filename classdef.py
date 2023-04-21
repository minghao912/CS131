from intbase import InterpreterBase
from helperclasses import Field, Method
from objdef import ObjectDefinition
import utils as utils

from typing import Callable, Dict, List

class ClassDefinition:
    def __init__(self, chunk: List[str | List[str]], error_callback: Callable[[str, str], None]):
        # Instance variables
        self.name = chunk[1]
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

        classbody = chunk[2:]

        for body_chunk in classbody:
            # Determine whether it's a method or field
            match body_chunk[0]:
                # Fields are in format (field field_name initial_value)
                case InterpreterBase.FIELD_DEF:
                    if body_chunk[1] in self.fields:
                        error_callback("Duplicate field", body_chunk[0].line_num)
                        return
                    else:
                        self.fields[body_chunk[1]] = Field(body_chunk[1], utils.parse_raw_value(body_chunk[2]))
                # Methods are in format [1]: name, [2]: params list, [3]: body
                case InterpreterBase.METHOD_DEF:
                    if body_chunk[1] in self.methods:
                        error_callback("Duplicate method", body_chunk[0].line_num)
                        return
                    else:
                        self.methods[body_chunk[1]] = Method(body_chunk[1], body_chunk[2], body_chunk[3])
                
    def instantiate_self(self) -> ObjectDefinition:
        obj = ObjectDefinition()

        # Add fields and methods
        for field in self.fields.values():
            obj.add_field(field)
        for method in self.methods.values():
            obj.add_method(method)

        return obj