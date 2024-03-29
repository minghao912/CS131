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
        # command has line_num property
        command = statement[0]
        match command:
            case InterpreterBase.BEGIN_DEF:
                substatements = statement[1:]
                return_initiated, return_field = self.__executor_begin(command.line_num, parameters, substatements, interpreter)
                return StatementReturn(return_initiated, return_field)

            case InterpreterBase.CALL_DEF:
                target_obj = statement[1]
                method_name = statement[2]
                method_args = statement[3:]

                function_return = self.__executor_call(command.line_num, parameters, target_obj, method_name, method_args, interpreter)
                return StatementReturn(False, function_return)

            case InterpreterBase.IF_DEF:
                function_return = self.__executor_if(command.line_num, parameters, statement[1:], interpreter)
                return StatementReturn(function_return[0], function_return[1])

            case InterpreterBase.INPUT_INT_DEF | InterpreterBase.INPUT_STRING_DEF:
                input_field = self.__executor_input(command.line_num, parameters, command, statement[1], interpreter)
                return StatementReturn(False, input_field)

            case InterpreterBase.PRINT_DEF:
                stuff_to_print = statement[1:]
                self.__executor_print(command.line_num, parameters, stuff_to_print, interpreter)
                return StatementReturn(False, None)

            case InterpreterBase.RETURN_DEF:
                if len(statement) < 2:
                    return StatementReturn(True, None)
                return StatementReturn(True, self.__executor_return(command.line_num, parameters, statement[1], interpreter))

            case InterpreterBase.SET_DEF:
                self.__executor_set(command.line_num, parameters, statement[1], statement[2], interpreter)
                return StatementReturn(False, None)

            case InterpreterBase.WHILE_DEF:
                function_return = self.__executor_while(command.line_num, parameters, statement[1], statement[2], interpreter)
                return StatementReturn(function_return[0], function_return[1])

            case InterpreterBase.NEW_DEF:
                new_object_def = self.__executor_new(command.line_num, parameters, statement[1], interpreter)
                return StatementReturn(False, new_object_def)

            case "+" | "-" | "*" | "/" | "%":
                arithmetic_result = self.__executor_arithmetic(command.line_num, parameters, command, statement[1:], interpreter)
                return StatementReturn(False, arithmetic_result)

            case "<" | ">" | "<=" | ">=" | "!=" | "==" | "&" | "|":
                comparison_result = self.__executor_compare(command.line_num, parameters, command, statement[1:], interpreter)
                return StatementReturn(False, comparison_result)

            case "!":
                notted_boolean = self.__executor_unary_not(command.line_num, parameters, statement[1], interpreter)
                return StatementReturn(False, notted_boolean)

            case _:
                interpreter.error(ErrorType.SYNTAX_ERROR, f"Unknown statement/expression: {command}", command.line_num)

    def __executor_begin(
        self, 
        line_num: int,
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
        line_num: int,
        method_params: Dict[str, Field], 
        target_obj: str, 
        method_name: str, 
        method_args: List[str], 
        interpreter: InterpreterBase
    ) -> Field:
        # Evaluate anything in args
        arg_values = list()
        for arg in method_args:
            arg_values.append(self.__executor_return(line_num, method_params, arg, interpreter))  # Re-use some code, does the same stuff

        other_obj: ObjectDefinition = None

        # Target object may be an expression
        if isinstance(target_obj, list):
            return_val = self.__executor_return(line_num, method_params, target_obj, interpreter).value
            if not isinstance(return_val, ObjectDefinition):
                interpreter.error(ErrorType.TYPE_ERROR, f"Expression does not return a class", line_num)
            else:
                other_obj = return_val
        # Target object is a variable or "me"
        else:
            # Call a method in my own object
            if target_obj == InterpreterBase.ME_DEF:
                return self.call_method(method_name, arg_values, interpreter)
            
            # Call a method in another object
            # Check to see if reference is valid
            if target_obj not in self.fields:
                interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {target_obj}", line_num)
            if self.fields[target_obj].type is Type.NULL:
                interpreter.error(ErrorType.FAULT_ERROR, f"Reference is null: {target_obj}", line_num)

            other_obj = self.fields[target_obj].value

        return other_obj.call_method(method_name, arg_values, interpreter)

    def __executor_if(
        self,
        line_num: int, 
        method_params: Dict[str, Field], 
        args: List[str], 
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        if len(args) != 2 and len(args) != 3:
            interpreter.error(ErrorType.SYNTAX_ERROR, "Too few or too many arguments for if statement", line_num)

        # Separate the arguments
        predicate = args[0]
        true_clause = args[1]
        false_clause = args[2] if len(args) == 3 else None

        # Evaluate predicate
        predicate_val: bool = None
        predicate_return: Field = self.__executor_return(line_num, method_params, predicate, interpreter)
        if predicate_return.type != Type.BOOL:
            interpreter.error(ErrorType.TYPE_ERROR, f"Predicate is not a boolean", line_num)
        else:
            predicate_val: bool = predicate_return.value
        
        # Run the correct clause
        if predicate_val:
            clause_return = self.__run_statement(method_params, true_clause, interpreter)
            return (clause_return.return_initiated, clause_return.return_field)
        else:
            if false_clause is not None:
                clause_return = self.__run_statement(method_params, false_clause, interpreter)
                return (clause_return.return_initiated, clause_return.return_field)
            else:
                return (False, None)

    def __executor_input(
        self,
        line_num: int, 
        method_params: Dict[str, Field], 
        command: str,
        var: str, 
        interpreter: InterpreterBase
    ) -> Field:
        # Check variable to read into exists
        if var not in self.fields:
            interpreter.error(ErrorType.NAME_ERROR, f"Unkonwn variable: {var}", line_num)

        # Read input
        user_input = interpreter.get_input()

        # Set to var
        read_in_int = (command == "inputi")
        self.fields[var].type = Type.INT if read_in_int else Type.STRING
        self.fields[var].value = int(user_input) if read_in_int else user_input

        return Field("temp", self.fields[var].type, self.fields[var].value)

    def __executor_print(
        self,  
        line_num: int,
        method_params: Dict[str, Field], 
        stuff_to_print: List[str], 
        interpreter: InterpreterBase
    ) -> None:
        # Special handling since Python uses "True/False" while Brewin uses "true/false" and "None" vs. null
        def __stringify(thing: Field) -> str:
            if thing.type == Type.BOOL:
                return InterpreterBase.TRUE_DEF if thing.value else InterpreterBase.FALSE_DEF
            elif thing.type == Type.NULL:
                return InterpreterBase.NULL_DEF
            else:
                return thing.value

        about_to_print = list()

        for expression in stuff_to_print:
            # Evaluate expression
            if isinstance(expression, list):
                statement_return = self.__run_statement(method_params, expression, interpreter)
                about_to_print.append(__stringify(statement_return.return_field))
            # Evaluate constant/literal or variable lookup
            else:
                raw_type, raw_thing = utils.parse_type_value(expression)

                append_this = None
                if raw_type is not None:
                    append_this = Field("temp", raw_type, raw_thing)
                else:
                    append_this = self.__get_var_value(line_num, expression, method_params, interpreter)

                about_to_print.append(__stringify(append_this))      

        final_string = "".join(map(str, about_to_print))
        interpreter.output(final_string)

    def __executor_return(
        self,  
        line_num: int,
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
            return self.__get_var_value(line_num, var_name, method_params, interpreter)

    def __executor_set(
        self,  
        line_num: int,
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
                interpreter.error(ErrorType.TYPE_ERROR, f"Cannot set variable to result of void function", line_num)
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
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}", line_num)

    def __executor_while(
        self,
        line_num: int, 
        method_params: Dict[str, Field], 
        predicate: str | List[str], 
        true_clause: List[str], 
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        if predicate is None or true_clause is None:
            interpreter.error(ErrorType.SYNTAX_ERROR, "Too few or too many arguments for if statement", line_num)

        # Evaluate predicate
        def __evaluate_predicate() -> bool:
            predicate_val: bool = None
            predicate_return: Field = self.__executor_return(line_num, method_params, predicate, interpreter)
            if predicate_return.type != Type.BOOL:
                interpreter.error(ErrorType.TYPE_ERROR, f"Predicate is not a boolean", line_num)
            else:
                predicate_val: bool = predicate_return.value
            return predicate_val
        
        # Run the correct clause
        while __evaluate_predicate():
            clause_return = self.__run_statement(method_params, true_clause, interpreter)
            if clause_return.return_initiated:
                return (clause_return.return_initiated, clause_return.return_field)
        else:
            return (False, None)

    def __executor_new(
        self,
        line_num: int, 
        method_params: Dict[str, Field], 
        arg: str, 
        interpreter: any # (Interpreter, but there is a circular dependency so ignore for now)
    ) -> Field:
        # Look for requested class
        other_class = interpreter.get_class(arg)
        if other_class is None:
            interpreter.error(ErrorType.TYPE_ERROR, f"Unknown class: {arg}", line_num)

        # Create a new object
        other_class_obj = other_class.instantiate_self()

        # Return object as field
        return Field("temp", Type.OBJ, other_class_obj)

    def __executor_arithmetic(
        self,  
        line_num: int,
        method_params: Dict[str, Field], 
        command: str, 
        args: List[Field],
        interpreter: InterpreterBase
    ) -> Field:
        if (len(args) > 2):
            interpreter.error(ErrorType.SYNTAX_ERROR, f"Invalid number of operands for operator: {command}", line_num)

        # Evaluate operands
        arg_values: List[Field] = list()
        for arg in args:
            arg_values.append(self.__executor_return(line_num, method_params, arg, interpreter))  # Re-use some code, does the same stuff

        # Operands can either be both strings (+) or both ints
        both_strings = False
        if command == "+" and arg_values[0].type == Type.STRING and arg_values[1].type == Type.STRING:
            both_strings = True
        elif arg_values[0].type == Type.INT and arg_values[1].type == Type.INT:
            pass
        else:
            interpreter.error(ErrorType.TYPE_ERROR, f"Operands of type '{arg_values[0].type}' and '{arg_values[1].type}' are incompatible with operator: {command}", line_num)

        result: str | int = None
        match command:
            case "+":
                # Only + can have string operands
                result = arg_values[0].value + arg_values[1].value
            case "-":
                result = arg_values[0].value - arg_values[1].value
            case "*":
                result = arg_values[0].value * arg_values[1].value
            case "/":
                result = arg_values[0].value // arg_values[1].value     # Int division
            case "%":
                result = arg_values[0].value % arg_values[1].value

        return Field("temp", Type.STRING if both_strings else Type.INT, result)

    def __executor_compare(
        self,  
        line_num: int,
        method_params: Dict[str, Field], 
        command: str, 
        args: List[Field],
        interpreter: InterpreterBase
    ) -> Field:
        if (len(args) > 2):
            interpreter.error(ErrorType.SYNTAX_ERROR, f"Invalid number of operands for operator: {command}", line_num)

        # Evaluate operands
        arg_values: List[Field] = list()
        for arg in args:
            arg_values.append(self.__executor_return(line_num, method_params, arg, interpreter))  # Re-use some code, does the same stuff

        # Operands can either be both strings or both ints
        int_string = [Type.INT, Type.STRING]
        int_string_bool = [Type.INT, Type.STRING, Type.BOOL]
        obj_null = [Type.NULL, Type.OBJ]
        just_bool = [Type.BOOL]

        if command in ["<", ">", "<=", ">="] and arg_values[0].type in int_string and arg_values[1].type in int_string:
            pass
        elif command in ["==", "!="] and arg_values[0].type in int_string_bool and arg_values[1].type in int_string_bool:
            pass
        elif command in ["==", "!="] and arg_values[0].type in obj_null and arg_values[1].type in obj_null:
            pass
        elif command in ["&", "|"] and arg_values[0].type in just_bool and arg_values[1].type in just_bool:
            pass
        else:
            interpreter.error(ErrorType.TYPE_ERROR, f"Operands of type '{arg_values[0].type}' and '{arg_values[1].type}' are incompatible with operator: {command}", line_num)

        # Do operation
        result: bool = None
        match command:
            # These only work for ints and strings
            case "<":
                result = arg_values[0].value < arg_values[1].value
            case ">":
                result = arg_values[0].value > arg_values[1].value
            case "<=":
                result = arg_values[0].value <= arg_values[1].value
            case ">=":
                result = arg_values[0].value >= arg_values[1].value

            # These work for ints, strings, and booleans
            case "==":
                result = arg_values[0].value == arg_values[1].value
            case "!=":
                result = arg_values[0].value != arg_values[1].value

            # These only work for booleans
            case "&":
                result = arg_values[0].value and arg_values[1].value
            case "|":
                result = arg_values[0].value or arg_values[1].value

        return Field("temp", Type.BOOL, result)

    def __executor_unary_not(
        self,  
        line_num: int,
        method_params: Dict[str, Field], 
        arg: str, 
        interpreter: InterpreterBase
    ) -> Field:
        arg_value = self.__executor_return(line_num, method_params, arg, interpreter)

        # Unary NOT only works on booleans
        if arg_value.type != Type.BOOL:
            interpreter.error(ErrorType.TYPE_ERROR, f"The operator '!' is not compatible with the type of variable '{arg}': {arg_value.type}", line_num)
        else:
            return Field("temp", Type.BOOL, not arg_value.value)

    def __get_var_value(
        self,  
        line_num: int,
        var_name: str, 
        method_params: Dict[str, Field], 
        interpreter: InterpreterBase
    ) -> Field:
        # A variable lookup
        if var_name in method_params:
            return method_params[var_name]
        # If not there, try finding it in the class fields
        elif var_name in self.fields:
            return self.fields[var_name]
        # If nowhere, return an error
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}", line_num)