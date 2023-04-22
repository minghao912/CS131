from inspect import trace
from intbase import ErrorType, InterpreterBase
from helperclasses import Field, Method
from objdef import ObjectDefinition
import utils as utils

from typing import Dict, List

class ClassDefinition:
    def __init__(self, chunk: List[str | List[str]], interpreter: InterpreterBase, trace_output: bool):
        # Instance variables
        self.name = chunk[1]
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

        self.trace_output = trace_output

        classbody = chunk[2:]

        for body_chunk in classbody:
            # Determine whether it's a method or field
            # body_chunk still has line_num var
            match body_chunk[0]:
                # Fields are in format (field field_name initial_value)
                case InterpreterBase.FIELD_DEF:
                    if body_chunk[1] in self.fields:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate field: {body_chunk[1]}", body_chunk[0].line_num)
                    else:
                        parsed_type, parsed_value = utils.parse_type_value(body_chunk[2])
                        self.fields[body_chunk[1]] = Field(body_chunk[1], parsed_type, parsed_value)
                # Methods are in format [1]: name, [2]: params list, [3]: body
                case InterpreterBase.METHOD_DEF:
                    if body_chunk[1] in self.methods:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate method: {body_chunk[1]}", body_chunk[0].line_num)
                    else:
                        self.methods[body_chunk[1]] = Method(body_chunk[1], body_chunk[2], body_chunk[3])
                
    def instantiate_self(self) -> ObjectDefinition:
        obj = ObjectDefinition(self.trace_output)

        # Add fields and methods
        for field in self.fields.values():
            obj.add_field(field)
        for method in self.methods.values():
            obj.add_method(method)

        return obj