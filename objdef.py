from distutils.log import error
from xmlrpc.client import Boolean
from intbase import InterpreterBase
from helperclasses import Field, Method

from typing import Callable, Dict, List, Optional, Tuple, final

class ObjectDefinition:
    def __init__(self):
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

    def add_method(self, method: Method):
        self.methods[method.name] = method

    def add_field(self, field: Field):
        self.fields[field.name] = field

    def call_method(self, methodName: str, parameters: List[any], error_callback: Callable[[str, str], None]):
        if not methodName in self.methods:
            error_callback("NAME", methodName, None)

        # Match parameters
        matched_parameters: Dict[str, any] = dict()
        required_paramters = self.methods[methodName].parameters
        passed_paramters = parameters

        if len(required_paramters) != len(passed_paramters):
            error_callback("TYPE", "Invalid number of parameters")

        for i in range(len(required_paramters)):
            matched_parameters[required_paramters[i]] = passed_paramters[i]

        # See if begin statement or just one
        methodBody = self.methods[methodName].body

        returned_value = None
        (return_issued, returned_value) = self.__run_statement(matched_parameters, methodBody, error_callback)
        if return_issued:
            return returned_value

        return returned_value

    # If returned boolean is True, a "return" has been issued
    def __run_statement(self, parameters: Dict[str, any], statement: List[str], error_callback: Callable[[str, str], None]) -> Tuple[Boolean, Optional[any]]:
        print(f"Passed parameters: {parameters}")
        print(f"Statement to execute: {statement}")

        # Run different handlers depending on the command
        command = statement[0]
        match command:
            case "begin":
                substatements = statement[1:]
                return self.__executor_begin(parameters, substatements, error_callback)

            case "call":
                return (False, "\"ASLFJLSDJFIOEJOIRSF\"")

            case "if":
                return (False, None)

            case "inputi" | "inputs":
                return (False, None)

            case "print":
                return (False, None)

            case "return":
                if len(statement) < 2:
                    return (True, None)
                return (True, self.__executor_return(parameters, statement[1], error_callback))

            case "set":
                self.__executor_set(parameters, statement[1], statement[2], error_callback)
                return (False, None)

            case "while":
                return (False, None)

    def __executor_begin(self, method_params: Dict[str, any], substatements: List[str], error_callback: Callable[[str, str], None]) -> any:
        returned_value = None
        for substatement in substatements:
            return_issued, returned_value = self.__run_statement(method_params, substatement, error_callback)
            if return_issued:
                return (True, returned_value)
        
        return (False, returned_value)

    def __executor_return(self, method_params: Dict[str, any], expr: str, error_callback: Callable[[str, str], None]) -> any:
        # Evaluate the expr expression, if applicable
        raw_value = None
        if isinstance(expr, list):
            raw_value = self.__run_statement(method_params, expr, error_callback)
        else:
            raw_value = self.__get_raw_value(expr)

        # Constant or literal
        if raw_value is not None:
            return raw_value
        
        # A variable lookup
        var_name = expr
        if var_name in method_params:
            return method_params[var_name].value
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            return self.fields[var_name].value
        # If nowhere, return an error
        else:
            error_callback("NAME", f"Unknown variable {var_name}")

    def __executor_set(self, method_params: Dict[str, any], var_name: str, new_val: any, error_callback: Callable[[str, str], None]):
        # Evaluate the new_val expression, if applicable
        set_to_this = None
        if isinstance(new_val, list):
            _, set_to_this = self.__run_statement(method_params, new_val, error_callback)
            if set_to_this is None:
                error_callback("TYPE", f"Cannot set variable to result of void function")
        else:
            set_to_this = self.__get_raw_value(new_val)

        # First try to find the variable in the method params (shadowing)
        if var_name in method_params:
            method_params[var_name] = set_to_this
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            self.fields[var_name] = set_to_this
        # If nowhere, return an error
        else:
            error_callback("NAME", f"Unknown variable {var_name}")

    def __get_raw_value(self, val: str) -> any:
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