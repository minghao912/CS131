from helperclasses import Type
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

def parse_type_from_str(type_name: str, current_class_list: List[str]) -> Type:
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
            # Check if it's a class
            if type_name in current_class_list:
                return Type.OBJ
            else:
                return None

def parse_value_given_type(type_name: str, val: str, current_class_list: List[str]) -> Tuple[Type | None, int | bool | None | str]:
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
            # Check if it's a class
            if type_name in current_class_list:
                return (Type.OBJ, type_name)
            else:
                return (None, None)