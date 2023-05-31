from intbase import ErrorType, InterpreterBase
from helperclasses import Field, Method, Type
from objdef import ObjectDefinition
import utils as utils

import copy
from typing import Dict, List, Self, Tuple

class ClassDefinition:
    def __init__(self, chunk: List[str | List[str]], superclass: Self | None, current_class_list: List[str], current_tclass_list: List[str], is_template_class: bool, interpreter: InterpreterBase, trace_output: bool):
        # Instance variables
        self.name = chunk[1]
        self.methods: Dict[str, List[Method]] = dict()
        self.fields: Dict[str, Field] = dict()
        self.superclass: ClassDefinition | None = superclass
        self.__current_class_list: List[str] = current_class_list
        self.__current_tclass_list: List[str] = current_tclass_list

        # For template classes
        self.is_template_class = is_template_class
        self.template_types: List[str] = None
        if is_template_class:
            self.template_types = chunk[2]
        else:
            self.template_types = []

        self.trace_output = trace_output

        classbody = chunk[2:] if not is_template_class else chunk[3:]

        for body_chunk in classbody:
            # Determine whether it's a method or field
            match body_chunk[0]:
                # Fields are in format (field field_type field_name initial_value)
                case InterpreterBase.FIELD_DEF:
                    field_type = body_chunk[1]
                    field_name = body_chunk[2]
                    init_value = body_chunk[3] if (len(body_chunk) >= 4) else None

                    if field_name in self.fields:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate field: {field_name}", body_chunk[0].line_num)
                    else:
                        # Initial value not provided, use default value
                        if init_value is None:
                            # For templated types, store temp var to be changed later
                            if is_template_class and field_type in self.template_types:
                                self.fields[field_name] = Field(field_name, Type.TUNINIT, None, field_type)
                            # For regular class, use default value
                            else:
                                parsed_type = utils.parse_type_from_str(field_type, self.__current_class_list + list(self.template_types), self.__current_tclass_list)
                                if parsed_type is None or parsed_type == Type.NULL:
                                    interpreter.error(ErrorType.TYPE_ERROR, f"Undeclared class '{field_type}'", body_chunk[0].line_num)

                                # If TCLASS, check if number of parameterized types is correct
                                if parsed_type == Type.TCLASS:
                                    base_tclass_name = field_type.split('@')[0]
                                    necessary_ptypes = \
                                        self.get_number_of_parameterized_types() if base_tclass_name == self.name \
                                        else interpreter.get_tclass(field_type.split('@')[0]).get_number_of_parameterized_types()
                                    actual_ptypes = len(field_type.split('@')) - 1

                                    if necessary_ptypes != actual_ptypes:
                                        interpreter.error(ErrorType.TYPE_ERROR, f"Incorrect number of parameterized types: Expected {necessary_ptypes} but got {actual_ptypes}")

                                # Set value as usual
                                default_init_value = utils.get_default_value(parsed_type)
                                self.fields[field_name] = Field(field_name, parsed_type, default_init_value, (field_type if parsed_type == Type.OBJ or parsed_type == Type.TCLASS else None))
                        # Initial value provided
                        else:
                            # For templated types, store init value to be type-checked later
                            if is_template_class and field_type in self.template_types:
                                self.fields[field_name] = Field(field_name, Type.TINIT, init_value, field_type)
                            # For regular class, use init value
                            else:
                                parsed_type, parsed_value = utils.parse_value_given_type(field_type, init_value, self.__current_class_list + list(self.template_types), self.__current_tclass_list)

                                # parsed_type will be none if an error occurred during value parsing (only possible error is incompatible type)
                                if parsed_type == None:
                                    interpreter.error(ErrorType.TYPE_ERROR, f"Incompatible type '{field_type}' with value '{init_value}'", body_chunk[0].line_num)
                                elif parsed_type == Type.NULL:
                                    interpreter.error(ErrorType.TYPE_ERROR, f"Undeclared class '{field_type if parsed_value is None else parsed_value}'", body_chunk[0].line_num)
                                elif parsed_type == Type.OBJ:
                                    self.fields[field_name] = Field(field_name, parsed_type, None, parsed_value)    # last member of "Field" only used for object names
                                elif parsed_type == Type.TCLASS:
                                    # Check if number of parameterized types is correct
                                    base_tclass_name = field_type.split('@')[0]
                                    necessary_ptypes = \
                                        self.get_number_of_parameterized_types() if base_tclass_name == self.name \
                                        else interpreter.get_tclass(field_type.split('@')[0]).get_number_of_parameterized_types()
                                    actual_ptypes = len(field_type.split('@')) - 1

                                    if necessary_ptypes != actual_ptypes:
                                        interpreter.error(ErrorType.TYPE_ERROR, f"Incorrect number of parameterized types: Expected {necessary_ptypes} but got {actual_ptypes}")

                                    self.fields[field_name] = Field(field_name, parsed_type, None, parsed_value)
                                else:
                                    self.fields[field_name] = Field(field_name, parsed_type, parsed_value)
                # Methods are in format [1] return_type, [2]: name, [3]: params list, [4]: body
                case InterpreterBase.METHOD_DEF:
                    method_return_type = body_chunk[1]
                    method_name = body_chunk[2]
                    method_params_list = body_chunk[3]
                    method_body = body_chunk[4]

                    # Parse method return type
                    method_return_type_partial: Type = utils.parse_type_from_str(method_return_type, self.__current_class_list + list(self.template_types), self.__current_tclass_list)
                    if method_return_type_partial == None:
                        interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type '{method_return_type}'", body_chunk[0].line_num)

                    method_return_type_parsed: Tuple[Type, str | None] = \
                        (method_return_type_partial, method_return_type) if method_return_type_partial == Type.OBJ \
                        else (method_return_type_partial, None)

                    # Parse each param's type (in format [0]: type, [1]: name)
                    method_params_list_parsed: List[Tuple[Type, str, str]] = []
                    for method_param in method_params_list:
                        # Check for duplicate param definition
                        def __param_already_exists(param_name: str, params_list: List[Tuple[Type, str, str]]) -> bool:
                            for p in params_list:
                                if p[1] == param_name:
                                    return True
                            else:
                                return False

                        if __param_already_exists(method_param[1], method_params_list_parsed):
                            interpreter.error(ErrorType.NAME_ERROR, f"Duplicate formal parameter '{method_param[1]}'", body_chunk[0].line_num)

                        mp_type = utils.parse_type_from_str(method_param[0], self.__current_class_list + list(self.template_types), self.__current_tclass_list)
                        if mp_type == None:
                            interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type '{mp_type}'", body_chunk[0].line_num)
                        else:
                            method_params_list_parsed.append(
                                (mp_type, method_param[1], method_param[0]) if mp_type == Type.OBJ \
                                else  (mp_type, method_param[1], None)
                            )

                    # Check duplicate method
                    # First check name
                    if method_name not in self.methods:
                        self.methods[method_name] = list()
                    # Check if overload
                    elif utils.get_correct_method(self.methods, method_name, list(map(lambda p: (p[0], p[2]), method_params_list_parsed)), interpreter) is None:
                        pass
                    else:
                        interpreter.error(ErrorType.NAME_ERROR, f"Duplicate method: {method_name}", body_chunk[0].line_num)

                    self.methods[method_name].append(Method(method_name, method_return_type_parsed, method_params_list_parsed, method_body))
                
    def instantiate_self(self) -> ObjectDefinition:
        obj = ObjectDefinition(self.trace_output)

        obj.set_class_name(self.name)
        obj.set_names_of_valid_classes(self.__current_class_list + list(self.template_types))
        obj.set_names_of_valid_tclasses(self.__current_tclass_list)
        obj.set_superclass((self.superclass).instantiate_self() if self.superclass is not None else None)

        # Non-template classes only
        if self.is_template_class:
            return None
        
        # Add fields and methods
        for field in self.fields.values():
            obj.add_field(copy.copy(field))
        for method_list in self.methods.values():
            obj.add_method(copy.deepcopy(method_list))

        return obj
    
    def instantiate_self_tclass(self, template_types_actual: List[str], interpreter: InterpreterBase) -> ObjectDefinition:
        obj = ObjectDefinition(self.trace_output)

        obj.set_class_name(self.name)
        obj.set_names_of_valid_classes(self.__current_class_list + list(self.template_types))
        obj.set_names_of_valid_tclasses(self.__current_tclass_list)
        obj.set_superclass((self.superclass).instantiate_self() if self.superclass is not None else None)

        # Non-template classes only
        if not self.is_template_class:
            return None
        
        # Replace template types with actual types
        matched_template_types = dict(zip(self.template_types, template_types_actual))

        def __get_new_field(old_field: Field, new_type: Type | str):
            if isinstance(new_type, str):
                return Field(old_field.name, Type.OBJ, old_field.value, new_type)
            else:
                return Field(old_field.name, new_type, old_field.value, None)

        for old_field in self.fields.values():
            new_field = copy.copy(old_field)

            field_was_init: bool = (old_field.type == Type.TINIT)
            field_was_uninit: bool = (old_field.type == Type.TUNINIT)

            # Replace templated types with actual types
            if new_field.obj_name in matched_template_types.keys():
                new_field = __get_new_field(new_field, matched_template_types[new_field.obj_name])

            # If field was previously uninitialized, we have to get default values now
            if field_was_uninit:
                default_init_value = utils.get_default_value(new_field.type)
                new_field = Field(new_field.name, new_field.type, default_init_value, new_field.obj_name)

            # If field was previously initialized, we have to do type check with new type
            if field_was_init:
                # Create field for init value
                init_value_type, init_value_value = utils.parse_type_value(old_field.value)
                if init_value_type is None or init_value_type == Type.NULL:
                    init_field = Field("temp_field_for_type_check", Type.OBJ, init_value_value, new_field.obj_name)
                else:
                    init_field = Field("temp_field_for_type_check", init_value_type, init_value_value, None)

                # Type check
                try:
                    utils.check_compatible_types(new_field, init_field, interpreter)
                except Exception as e:
                    interpreter.error(ErrorType.TYPE_ERROR, f"Invalid initial value '{init_field.value}' for field '{new_field.name}': {str(e)}")

            obj.add_field(new_field)

        for method_list in self.methods.values():
            new_methods = copy.deepcopy(method_list)

            for new_method in new_methods:
                # Replace return type
                if new_method.return_type[1] in matched_template_types.keys():
                    new_ret_type_temp_field = __get_new_field(Field("temp_replace_ret_type", new_method.return_type[0], None, new_method.return_type[1]), matched_template_types[new_method.return_type[1]])
                    new_method.return_type = (new_ret_type_temp_field.type, new_ret_type_temp_field.obj_name)
                
                # Replace param types
                for i, method_param in enumerate(new_method.parameters):
                    if method_param[2] is not None and method_param[2] in matched_template_types.keys():
                        new_param_temp_field = __get_new_field(Field(method_param[1], method_param[0], None, method_param[2]), matched_template_types[method_param[2]])
                        new_method.parameters[i] = (new_param_temp_field.type, new_param_temp_field.name, new_param_temp_field.obj_name)

                # Replace references in actual body
                def __find_and_replace(body: List[str], find_replace: Dict[str, str]):
                    for i, body_part in enumerate(body):
                        if isinstance(body_part, list):
                            __find_and_replace(body_part, find_replace)
                        else:
                            if body_part in find_replace.keys():
                                body[i] = find_replace[body_part]

                __find_and_replace(new_method.body, matched_template_types)

            obj.add_method(new_methods)
        
        return obj
    
    def get_number_of_parameterized_types(self) -> int:
        return len(self.template_types)