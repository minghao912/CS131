def parse_raw_value(val: str) -> int | bool | None | str:
    final_val = None

    # Check if int
    try:
        final_val = int(val)
    except ValueError:
        val_lower = val.lower()
        # Check boolean
        if val_lower == "true":
            final_val = True
        elif val_lower == "false":
            final_val = False

        # Check null
        elif val_lower == "null":
            final_val = None

        # Check string
        elif '"' in val:
            final_val = val[1:-1]
    finally:
        return final_val