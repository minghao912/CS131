from dataclasses import dataclass
from intbase import ErrorType, InterpreterBase
from helperclasses import Field, Method, Type
import utils as utils

from typing import Dict, List, Tuple

@dataclass
class StatementReturn:
    return_initiated: bool
    return_field: Field

class ObjectDefinition:
    def __init__(self, trace_output: bool):
        self.methods: Dict[str, Method] = dict()
        self.fields: Dict[str, Field] = dict()

        self.trace_output = trace_output

    def add_method(self, method: Method):
        self.methods[method.name] = method

    def add_field(self, field: Field):
        self.fields[field.name] = field

    def call_method(
        self, 
        methodName: str, 
        parameters: List[Field], 
        interpreter: InterpreterBase
    ) -> Field:
        if not methodName in self.methods:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown method: {methodName}")

        # Match parameters
        matched_parameters: Dict[str, any] = dict()
        required_parameters = self.methods[methodName].parameters
        passed_paramters = parameters

        if len(required_parameters) != len(passed_paramters):
            interpreter.error(ErrorType.TYPE_ERROR, f"Invlalid number of parameters for method: {methodName}")

        for i in range(len(required_parameters)):
            matched_parameters[required_parameters[i]] = Field(required_parameters[i], passed_paramters[i].type, passed_paramters[i].value)

        # See if begin statement or just one
        methodBody = self.methods[methodName].body

        statement_return = self.__run_statement(matched_parameters, methodBody, interpreter)
        return statement_return.return_field

    # If returned bool is True, a "return" has been issued
    def __run_statement(
        self, 
        parameters: Dict[str, Field], 
        statement: List[str], 
        interpreter: InterpreterBase
    ) -> StatementReturn:

        if self.trace_output:
            print(f"Passed parameters: {parameters}")
            print(f"Statement to execute: {statement}")

        # Run different handlers depending on the command
        command = statement[0]
        match command:
            case InterpreterBase.BEGIN_DEF:
                substatements = statement[1:]
                return_initiated, return_field = self.__executor_begin(parameters, substatements, interpreter)
                return StatementReturn(return_initiated, return_field)

            case InterpreterBase.CALL_DEF:
                target_obj = statement[1]
                method_name = statement[2]
                method_args = statement[3:]

                function_return = self.__executor_call(parameters, target_obj, method_name, method_args, interpreter)
                return StatementReturn(False, function_return)

            case InterpreterBase.IF_DEF:
                return StatementReturn(False, None)

            case InterpreterBase.INPUT_INT_DEF | InterpreterBase.INPUT_STRING_DEF:
                return StatementReturn(False, None)

            case InterpreterBase.PRINT_DEF:
                stuff_to_print = statement[1:]
                self.__executor_print(parameters, stuff_to_print, interpreter)
                return StatementReturn(False, None)

            case InterpreterBase.RETURN_DEF:
                if len(statement) < 2:
                    return StatementReturn(True, None)
                return StatementReturn(True, self.__executor_return(parameters, statement[1], interpreter))

            case InterpreterBase.SET_DEF:
                self.__executor_set(parameters, statement[1], statement[2], interpreter)
                return StatementReturn(False, None)

            case InterpreterBase.WHILE_DEF:
                return StatementReturn(False, None)

            case InterpreterBase.NEW_DEF:
                return StatementReturn(False, None)

            case "+" | "-" | "*" | "/" | "%":
                return StatementReturn(False, None)

            case "<" | ">" | "<=" | ">=":
                return StatementReturn(False, None)
            
            case "!=" | "==" | "&" | "|":
                return StatementReturn(False, None)

            case "!":
                notted_boolean = self.__executor_unary_not(parameters, statement[1], interpreter)
                return StatementReturn(False, notted_boolean)

            case _:
                interpreter.error(ErrorType.SYNTAX_ERROR, f"Unknown statement/expression: {command}")

    def __executor_begin(
        self, 
        method_params: Dict[str, Field], 
        substatements: List[str], 
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        statement_return = None
        for substatement in substatements:
            statement_return = self.__run_statement(method_params, substatement, interpreter)
            if statement_return.return_initiated:
                return (True, statement_return.return_field)
        
        return (False, statement_return.return_field)

    def __executor_call(
        self, 
        method_params: Dict[str, Field], 
        target_obj: str, 
        method_name: str, 
        method_args: List[str], 
        interpreter: InterpreterBase
    ) -> Field:
        # Evaluate anything in args
        arg_values = list()
        for arg in method_args:
            arg_values.append(self.__executor_return(method_params, arg, interpreter))  # Re-use some code, does the same stuff

        # Call a method in my own object
        if target_obj == InterpreterBase.ME_DEF:
            return self.call_method(method_name, arg_values, interpreter)
        
        # Call a method in another object
        # Check to see if reference is valid
        if target_obj not in self.fields:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {target_obj}")
        if self.fields[target_obj].type is Type.NULL:
            interpreter.error(ErrorType.FAULT_ERROR, f"Reference is null: {target_obj}")

        other_obj: ObjectDefinition = self.fields[target_obj].value
        return other_obj.call_method(method_name, arg_values, interpreter)

    def __executor_print(
        self, 
        method_params: Dict[str, Field], 
        stuff_to_print: List[str], 
        interpreter: InterpreterBase
    ) -> None:
        about_to_print = list()

        for expression in stuff_to_print:
            # Evaluate expression
            if isinstance(expression, list):
                statement_return = self.__run_statement(method_params, expression, interpreter)
                about_to_print.append(statement_return.return_field.value)
            # Evaluate constant/literal or variable lookup
            else:
                raw_type, raw_thing = utils.parse_type_value(expression)

                append_this = None
                if raw_type is not None:
                    append_this = Field("temp", raw_type, raw_thing)
                else:
                    append_this = self.__get_var_value(expression, method_params, interpreter)

                # Special handling since Python uses "True/False" while Brewin uses "true/false" and "None" vs. null
                if append_this.type == Type.BOOL:
                    about_to_print.append(InterpreterBase.TRUE_DEF if append_this.value else InterpreterBase.FALSE_DEF)
                elif append_this.type == Type.NULL:
                    about_to_print.append(InterpreterBase.NULL_DEF)
                else:
                    about_to_print.append(append_this.value)

        final_string = "".join(map(str, about_to_print))
        interpreter.output(final_string)

    def __executor_return(
        self, 
        method_params: Dict[str, Field], 
        expr: str, 
        interpreter: InterpreterBase
    ) -> Field:
        # Evaluate the expr expression, if applicable
        if isinstance(expr, list):
            statement_return = self.__run_statement(method_params, expr, interpreter)
            return statement_return.return_field

        # Not an expression, can be constant/literal or variable name
        else:
            raw_type, raw_value = utils.parse_type_value(expr)

            # Constant or literal
            if raw_type is not None:
                return Field("temp", raw_type, raw_value)
            
            # A variable lookup
            var_name = expr
            return self.__get_var_value(var_name, method_params, interpreter)

    def __executor_set(
        self, 
        method_params: Dict[str, Field], 
        var_name: str, 
        new_val: any, 
        interpreter: InterpreterBase
    ) -> None:
        # Evaluate the new_val expression, if applicable
        set_to_this = (None, None)
        if isinstance(new_val, list):
            statement_return = self.__run_statement(method_params, new_val, interpreter)
            if statement_return.return_field is None:
                interpreter.error(ErrorType.TYPE_ERROR, f"Cannot set variable to result of void function")
            else:
                set_to_this = (statement_return.return_field.type, statement_return.return_field.value)
        # Get the constant/literal or variable
        else:
            set_to_this = utils.parse_type_value(new_val)

        # First try to find the variable in the method params (shadowing)
        if var_name in method_params:
            method_params[var_name].type = set_to_this[0]
            method_params[var_name].value = set_to_this[1]
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            self.fields[var_name].type = set_to_this[0]
            self.fields[var_name].value = set_to_this[1]
        # If nowhere, return an error
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}")

    def __executor_unary_not(self, method_params: Dict[str, Field], arg: str, interpreter: InterpreterBase) -> Field:
        arg_value = self.__executor_return(method_params, arg, interpreter)

        # Unary NOT only works on booleans
        if arg_value.type != Type.BOOL:
            interpreter.error(ErrorType.TYPE_ERROR, f"The operator '!' is not compatible with the type of variable '{arg}': {arg_value.type}")
        else:
            return Field("temp", Type.BOOL, not arg_value.value)

    def __get_var_value(self, var_name: str, method_params: Dict[str, Field], interpreter: InterpreterBase) -> Field:
        # A variable lookup
        if var_name in method_params:
            return method_params[var_name]
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            return self.fields[var_name]
        # If nowhere, return an error
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}")