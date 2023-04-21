from distutils.log import error
from xmlrpc.client import Boolean
from intbase import InterpreterBase
from helperclasses import Field, Method
import utils as utils

from typing import Callable, Dict, List, Optional, Tuple, final

class ObjectDefinition:
    def __init__(self):
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

    def add_method(self, method: Method):
        self.methods[method.name] = method

    def add_field(self, field: Field):
        self.fields[field.name] = field

    def call_method(
        self, 
        methodName: str, 
        parameters: List[any], 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None]
    ):
        if not methodName in self.methods:
            error_callback("NAME", f"Unknown method {methodName}")

        # Match parameters
        matched_parameters: Dict[str, any] = dict()
        required_parameters = self.methods[methodName].parameters
        passed_paramters = parameters

        if len(required_parameters) != len(passed_paramters):
            error_callback("TYPE", f"Invalid number of parameters for method {methodName}")

        for i in range(len(required_parameters)):
            matched_parameters[required_parameters[i]] = Field(required_parameters[i], passed_paramters[i])

        # See if begin statement or just one
        methodBody = self.methods[methodName].body

        returned_value = None
        (return_issued, returned_value) = self.__run_statement(matched_parameters, methodBody, error_callback, print_callback)
        if return_issued:
            return returned_value

        return returned_value

    # If returned boolean is True, a "return" has been issued
    def __run_statement(
        self, 
        parameters: Dict[str, Field], 
        statement: List[str], 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None] | None = None
    ) -> Tuple[Boolean, Optional[any]]:
        print(f"Passed parameters: {parameters}")
        print(f"Statement to execute: {statement}")

        # Run different handlers depending on the command
        command = statement[0]
        match command:
            case "begin":
                substatements = statement[1:]
                return self.__executor_begin(parameters, substatements, error_callback, print_callback)

            case "call":
                target_obj = statement[1]
                method_name = statement[2]
                method_args = statement[3:]

                function_return = self.__executor_call(parameters, target_obj, method_name, method_args, error_callback, print_callback)
                return (False, function_return)

            case "if":
                return (False, None)

            case "inputi" | "inputs":
                return (False, None)

            case "print":
                stuff_to_print = statement[1:]
                self.__executor_print(parameters, stuff_to_print, error_callback, print_callback)
                return (False, None)

            case "return":
                if len(statement) < 2:
                    return (True, None)
                return (True, self.__executor_return(parameters, statement[1], error_callback, print_callback))

            case "set":
                self.__executor_set(parameters, statement[1], statement[2], error_callback, print_callback)
                return (False, None)

            case "while":
                return (False, None)

    def __executor_begin(
        self, 
        method_params: Dict[str, Field], 
        substatements: List[str], 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None]
    ) -> Tuple[Boolean, Optional[any]]:
        returned_value = None
        for substatement in substatements:
            return_issued, returned_value = self.__run_statement(method_params, substatement, error_callback, print_callback)
            if return_issued:
                return (True, returned_value)
        
        return (False, returned_value)

    def __executor_call(
        self, 
        method_params: Dict[str, Field], 
        target_obj: str, 
        method_name: str, 
        method_args: List[str], 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None]
    ) -> any:
        # Evaluate anything in args
        arg_values = list()
        for arg in method_args:
            arg_values.append(self.__executor_return(method_params, arg, error_callback, print_callback))  # Re-use some code, does the same stuff

        # Call a method in my own object
        if target_obj == "me":
            return self.call_method(method_name, arg_values, error_callback, print_callback)
        
        # Call a method in another object
        # Check to see if reference is valid
        if target_obj not in self.fields:
            error_callback("NAME", f"Unknown variable {target_obj}")
        if self.fields[target_obj].value is None:
            error_callback("FAULT", f"Reference {target_obj} is null")

        other_obj: ObjectDefinition = self.fields[target_obj].value
        return other_obj.call_method(method_name, arg_values, error_callback, print_callback)

    def __executor_print(
        self, 
        method_params: Dict[str, Field], 
        stuff_to_print: List[str], 
        error_callback: Callable[[str, str], None], 
        print_callback: Callable[[str], None]
    ) -> None:
        about_to_print = list()

        for expression in stuff_to_print:
            raw_thing = None
            if isinstance(expression, list):
                _, raw_thing = self.__run_statement(method_params, expression, error_callback, print_callback)
            else:
                raw_thing = utils.parse_raw_value(expression)

            if raw_thing is not None:
                about_to_print.append(raw_thing)
            else:
                about_to_print.append(self.__get_var_value(method_params, raw_thing, error_callback))

        final_string = "".join(map(str, about_to_print))
        print_callback(final_string)
        

    def __executor_return(
        self, 
        method_params: Dict[str, Field], 
        expr: str, 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None]
    ) -> any:
        # Evaluate the expr expression, if applicable
        raw_value = None
        if isinstance(expr, list):
            _, raw_value = self.__run_statement(method_params, expr, error_callback, print_callback)
        else:
            raw_value = utils.parse_raw_value(expr)

        # Constant or literal
        if raw_value is not None:
            return raw_value
        
        # A variable lookup
        var_name = expr
        return self.__get_var_value(var_name, method_params, error_callback)

    def __executor_set(
        self, 
        method_params: Dict[str, Field], 
        var_name: str, 
        new_val: any, 
        error_callback: Callable[[str, str], None],
        print_callback: Callable[[str], None]
    ):
        # Evaluate the new_val expression, if applicable
        set_to_this = None
        if isinstance(new_val, list):
            _, set_to_this = self.__run_statement(method_params, new_val, error_callback, print_callback)
            if set_to_this is None:
                error_callback("TYPE", f"Cannot set variable to result of void function")
        else:
            set_to_this = utils.parse_raw_value(new_val)

        # First try to find the variable in the method params (shadowing)
        if var_name in method_params:
            method_params[var_name].value = set_to_this
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            self.fields[var_name].value = set_to_this
        # If nowhere, return an error
        else:
            error_callback("NAME", f"Unknown variable {var_name}")

    def __get_var_value(self, var_name: str, method_params: Dict[str, Field], error_callback: Callable[[str, str], None]) -> any:
        # A variable lookup
        if var_name in method_params:
            return method_params[var_name].value
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            return self.fields[var_name].value
        # If nowhere, return an error
        else:
            error_callback("NAME", f"Unknown variable {var_name}")