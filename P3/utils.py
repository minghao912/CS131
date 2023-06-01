from helperclasses import Field, Method, Type
from intbase import InterpreterBase

from typing import List, Tuple

def parse_type_value(val: str) -> Tuple[Type | None, int | bool | None | str]:
    final_val = (None, None)

    # Check if int
    try:
        int_val = int(val)
        final_val = (Type.INT, int_val)
    except ValueError:
        val_lower = val.lower()
        # Check boolean
        if val_lower == "true":
            bool_val = True
            final_val = (Type.BOOL, bool_val)
        elif val_lower == "false":
            bool_val = False
            final_val = (Type.BOOL, bool_val)

        # Check null
        elif val_lower == "null":
            final_val = (Type.NULL, None)

        # Check string
        elif '"' in val:
            final_val = (Type.STRING, val[1:-1])
    finally:
        return final_val

def parse_type_from_str(type_name: str, current_class_list: List[str], template_class_list: List[str]) -> Type:
    match type_name:
        case InterpreterBase.INT_DEF:
            return Type.INT
        case InterpreterBase.BOOL_DEF:
            return Type.BOOL
        case InterpreterBase.STRING_DEF:
            return Type.STRING
        case InterpreterBase.VOID_DEF:
            return Type.NULL
        case _:
            # Check if it's a template class
            if (first_at_sign := type_name.find('@')) != -1:
                # Check if it's already a defined class
                if type_name in current_class_list:
                    return Type.OBJ
                else:
                    temp_type_name = type_name[first_at_sign + 1:]
                    # Check if the template types are valid classes
                    while (next_at_sign := temp_type_name.find('@')) != -1:
                        if parse_type_from_str(temp_type_name[:next_at_sign], current_class_list, template_class_list) is None:
                            return None
                        temp_type_name = temp_type_name[next_at_sign + 1:]
                    else:
                        if parse_type_from_str(temp_type_name, current_class_list, template_class_list) is None:
                            return None
                        return Type.TCLASS
                
            # Check if valid class
            if type_name in current_class_list:
                return Type.OBJ
            # Check if tclass
            elif type_name in template_class_list:
                return None # Cannot have tclass without @
            else:
                return None

def parse_value_given_type(type_name: str, val: str, current_class_list: List[str], template_class_list: List[str]) -> Tuple[Type | None, int | bool | None | str]:
    match type_name:
        case InterpreterBase.INT_DEF:
            try:
                int_val = int(val)
                return (Type.INT, int_val)
            except ValueError:
                return (None, None)
        case InterpreterBase.BOOL_DEF:
            val_lower = val.lower()
            # Check boolean
            if val_lower == "true":
                return (Type.BOOL, True)
            elif val_lower == "false":
                return (Type.BOOL, False)
            else:
                return (None, None)
        case InterpreterBase.STRING_DEF:
            if '"' in val:
                return (Type.STRING, val[1:-1])
            else:
                return (None, None)
        case _:
            # Check if it's a template class
            if (first_at_sign := type_name.find('@')) != -1:
                # Check if it's already a defined class
                if type_name in current_class_list:
                    return (Type.OBJ, type_name)
                else:
                    temp_type_name = type_name[first_at_sign + 1:]
                    # Check if the template types are valid classes
                    while (next_at_sign := temp_type_name.find('@')) != -1:
                        if parse_type_from_str(temp_type_name[:next_at_sign], current_class_list, template_class_list) is None:
                            return (Type.NULL, temp_type_name[:next_at_sign])
                        temp_type_name = temp_type_name[next_at_sign + 1:]
                    else:
                        if parse_type_from_str(temp_type_name, current_class_list, template_class_list) is None:
                            return (Type.NULL, temp_type_name[:next_at_sign])
                        return (Type.TCLASS, type_name)

            # Check if it's a normal class
            if type_name in current_class_list:
                return (Type.OBJ, type_name)
            # Check if it's a tclass (no @ -- this should be an error but do not throw it here)
            elif type_name in template_class_list:
                return (Type.TCLASS, type_name)
            else:
                return (Type.NULL, None)    # Signals undeclared class

def check_compatible_types(field1: Field, field2: Field, interpreter: InterpreterBase) -> bool:
    # Check compatible types
    if field1.type in [Type.OBJ, Type.TCLASS] and field2.type in [Type.OBJ, Type.TCLASS, Type.NULL]:
        if field2.type == Type.NULL: # Any object can be set to null
            return True
        elif field1.obj_name == field2.obj_name:   # For objects, compare the object name
            return True
        # Allow polymorphism
        elif field2.value is None:
            # We are getting a none value, so need to create a dummy object to ask if it inherits
            dummy_class = interpreter.get_class(field2.obj_name)
            if dummy_class is not None:
                dummy_obj = dummy_class.instantiate_self()
                if dummy_obj.inherits(field1.obj_name):
                    return True
                else:
                    raise Exception(f"Expected object of type '{field1.obj_name}' but got '{field2.obj_name}' instead")
            else:
                raise Exception(f"Type '{field2.obj_name}' does not exist")
        elif field2.value.inherits(field1.obj_name):   
            return True
        else:
            raise Exception(f"Expected object of type '{field1.obj_name}' but got '{field2.obj_name}' instead")
    elif field1.type == field2.type:    # For everything else, compare type
        return True
    else:
        raise Exception(f"Expected {field1.type} but got {field2.type} instead")

def get_default_value(return_type: Type) -> int | bool | str | None:
    match return_type:
        case Type.INT:
            return 0
        case Type.BOOL:
            return False
        case Type.STRING:
            return ""
        case Type.OBJ:
            return None
        case Type.NULL:
            return None
        case Type.TCLASS:
            return None
        case _:
            raise Exception(f"Not a valid type '{return_type}'!")

def get_method_type_list(method_params: List[Tuple[Type, str, str]]) -> List[Tuple[Type, str]]:
    return map(
        lambda tuple: (tuple[0], tuple[2]),
        method_params
    )

def get_correct_method(methods_list: List[Method], method_name: str, params: List[Tuple[Type, str, any]], interpreter: InterpreterBase) -> Method | None:
    # Check for the correct method signature
    for m in methods_list[method_name]:
        if len(m.parameters) != len(params):
            continue
        
        for (mp_type, pp_type) in zip(get_method_type_list(m.parameters), params):
            try:
                check_compatible_types(Field("temp", mp_type[0], None, mp_type[1]), Field("temp", pp_type[0], pp_type[2], pp_type[1]), interpreter)
            except Exception as e:
                break
        else:
            return m
    else:
        return None