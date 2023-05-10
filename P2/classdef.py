from dataclasses import field
from intbase import ErrorType, InterpreterBase
from helperclasses import Field, Method, Type
from objdef import ObjectDefinition
import utils as utils

from typing import Dict, List, Tuple

class ClassDefinition:
    def __init__(self, chunk: List[str | List[str]], current_class_list: List[str], interpreter: InterpreterBase, trace_output: bool):
        # Instance variables
        self.name = chunk[1]
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

        self.trace_output = trace_output

        classbody = chunk[2:]

        for body_chunk in classbody:
            # Determine whether it's a method or field
            match body_chunk[0]:
                # Fields are in format (field field_type field_name initial_value)
                case InterpreterBase.FIELD_DEF:
                    field_type = body_chunk[1]
                    field_name = body_chunk[2]
                    init_value = body_chunk[3]

                    if field_name in self.fields:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate field: {field_name}", body_chunk[0].line_num)
                    else:
                        parsed_type, parsed_value = utils.parse_value_given_type(field_type, init_value, current_class_list)

                        # parsed_type will be none if an error occurred during value parsing (only possible error is incompatible type)
                        if parsed_type == None:
                            interpreter.error(ErrorType.TYPE_ERROR, f"Incompatible type '{field_type}' with value '{init_value}'", body_chunk[0].line_num)
                        elif parsed_type == Type.OBJ:
                            self.fields[field_name] = Field(field_name, parsed_type, None, parsed_value)    # last member of "Field" only used for object names
                        else:
                            self.fields[field_name] = Field(field_name, parsed_type, parsed_value)
                # Methods are in format [1] return_type, [2]: name, [3]: params list, [4]: body
                case InterpreterBase.METHOD_DEF:
                    method_return_type = body_chunk[1]
                    method_name = body_chunk[2]
                    method_params_list = body_chunk[3]
                    method_body = body_chunk[4]

                    if method_name in self.methods:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate method: {body_chunk[1]}", body_chunk[0].line_num)
                    else:
                        # Parse method return type
                        method_return_type_parsed = utils.parse_type_from_str(method_return_type, current_class_list)
                        if method_return_type_parsed == None:
                            interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type '{method_return_type}'", body_chunk[0].line_num)
                        else:
                            # Parse each param's type (in format [0]: type, [1]: name)
                            method_params_list_parsed: List[Tuple[Type, str]] = []
                            for method_param in method_params_list:
                                mp_type = utils.parse_type_from_str(method_param[0], current_class_list)
                                if mp_type == None:
                                    interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type '{mp_type}'", body_chunk[0].line_num)
                                else:
                                    method_params_list_parsed.append((mp_type, method_param[1]))

                            self.methods[method_name] = Method(method_name, method_return_type_parsed, method_params_list_parsed, method_body)
                
    def instantiate_self(self) -> ObjectDefinition:
        obj = ObjectDefinition(self.trace_output)

        # Add fields and methods
        for field in self.fields.values():
            obj.add_field(field)
        for method in self.methods.values():
            obj.add_method(method)

        return obj