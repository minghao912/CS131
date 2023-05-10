from helperclasses import Type

from typing import Tuple

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