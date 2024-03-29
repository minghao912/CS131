from dataclasses import dataclass
from intbase import ErrorType, InterpreterBase
from helperclasses import Field, Method, Type
import utils as utils

from typing import Dict, List, Self, Tuple

@dataclass
class StatementReturn:
    return_initiated: bool
    return_field: Field

class ObjectDefinition:
    def __init__(self, trace_output: bool):
        self.methods: Dict[str, List[Method]] = dict()
        self.fields: Dict[str, Field] = dict()
        self.class_name: str = None
        self.superclass: ObjectDefinition | None = None
        self.__names_of_valid_classes: List[str] = []
        self.__names_of_valid_tclasses: List[str] = []

        self.trace_output = trace_output

    def set_class_name(self, class_name: str):
        self.class_name = class_name

    def set_superclass(self, superclass: Self):
        self.superclass = superclass

    def set_names_of_valid_classes(self, names_of_valid_classes: List[str]):
        self.__names_of_valid_classes = names_of_valid_classes

    def set_names_of_valid_tclasses(self, names_of_valid_tclasses: List[str]):
        self.__names_of_valid_tclasses = names_of_valid_tclasses

    def add_method(self, method_list: List[Method]):
        self.methods[method_list[0].name] = method_list

    def add_field(self, field: Field):
        self.fields[field.name] = field

    def call_method(
        self, 
        methodName: str, 
        parameters: List[Field], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Field:
        obj_to_call: Self = None
        method_to_call: Method = None
        if (found := self.get_method_from_polymorphic_methods(methodName, parameters, interpreter)) is not None:
            obj_to_call = found[0]
            method_to_call = found[1]
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Matching method '{methodName}' not found")

        # Match parameters
        matched_parameters: Dict[str, any] = dict()
        required_parameters = method_to_call.parameters
        passed_paramters = parameters

        if len(required_parameters) != len(passed_paramters):
            interpreter.error(ErrorType.TYPE_ERROR, f"Invlalid number of parameters for method: {methodName}")

        # Match parameters, doing type check
        def _param_matcher(req_param: Tuple[Type, str, str], pass_param: Field) -> Field:
            # Type check
            try:
                utils.check_compatible_types(Field(req_param[1], req_param[0], None, req_param[2]), pass_param, interpreter)
            except Exception as e:
                interpreter.error(ErrorType.NAME_ERROR, f"Invalid type for parameter '{req_param[1]}' of method '{methodName}': {str(e)}")
            
            # Final field creation
            return Field(req_param[1], req_param[0], pass_param.value, req_param[2])

        matched_parameters = {
            req_param[1]: _param_matcher(req_param, pass_param)
            for (req_param, pass_param) in zip(required_parameters, passed_paramters)
        }

        # See if begin statement or just one
        methodBody = method_to_call.body
        methodReturnType = method_to_call.return_type

        # Add self to calling stack if not already there
        if calling_class_list[-1] is not self:
            calling_class_list.append(self)
        statement_return = obj_to_call.__run_statement([matched_parameters], methodReturnType, methodBody, calling_class_list, interpreter)

        # Set default return value, if applicable
        if statement_return.return_field is None or statement_return.return_field.value is None:
            statement_return.return_field = Field(
                "temp", 
                methodReturnType[0], 
                utils.get_default_value(methodReturnType[0]),
                methodReturnType[1]
            )

        return statement_return.return_field

    def get_var_from_polymorphic_fields(self, var_name: str) -> Field | None:
        if var_name in self.fields:
            return self.fields[var_name]
        else:
            return None
            """ FIELDS ARE PRIVATE NOT PROTECTED
            if self.superclass is None:
                return None
            else:
                return self.superclass.get_var_from_polymorphic_fields(var_name) """

    def get_method_from_polymorphic_methods(self, method_name: str, params: List[Field], interpreter: InterpreterBase) -> Tuple[Self, Method | None]:
        # Check method of this name exists
        if method_name in self.methods:
            found_method = utils.get_correct_method(self.methods, method_name, list(map(lambda f: (f.type, f.obj_name, f.value), params)), interpreter)
            if found_method is not None:
                return (self, found_method)

        if self.superclass is None:
            return None
        else:
            return self.superclass.get_method_from_polymorphic_methods(method_name, params, interpreter)

    def inherits(self, other_class_name: str) -> bool:
        if self.class_name == other_class_name:
            return True
        elif self.superclass is None:
            return False
        else:
            if self.superclass.class_name == other_class_name:
                return True
            else:
                return self.superclass.inherits(other_class_name)

    # If returned bool is True, a "return" has been issued
    def __run_statement(
        self, 
        parameters: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        statement: List[str], 
        calling_class_list: List[Self],
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
                return_initiated, return_field = self.__executor_begin(command.line_num, parameters, method_return_type, substatements, calling_class_list, interpreter)
                return StatementReturn(return_initiated, return_field)

            case InterpreterBase.CALL_DEF:
                target_obj = statement[1]
                method_name = statement[2]
                method_args = statement[3:]

                return_initiated, function_return = self.__executor_call(command.line_num, parameters, target_obj, method_name, method_args, calling_class_list, interpreter)
                return StatementReturn(return_initiated, function_return)

            case InterpreterBase.IF_DEF:
                function_return = self.__executor_if(command.line_num, parameters, method_return_type, statement[1:], calling_class_list, interpreter)
                return StatementReturn(function_return[0], function_return[1])

            case InterpreterBase.INPUT_INT_DEF | InterpreterBase.INPUT_STRING_DEF:
                input_field = self.__executor_input(command.line_num, parameters, command, statement[1], interpreter)
                return StatementReturn(False, input_field)

            case InterpreterBase.PRINT_DEF:
                stuff_to_print = statement[1:]
                return_initiated, return_field = self.__executor_print(command.line_num, parameters, method_return_type, stuff_to_print, calling_class_list, interpreter)
                return StatementReturn(return_initiated, return_field)

            case InterpreterBase.RETURN_DEF:
                if len(statement) < 2:
                    return StatementReturn(True, None)
                return StatementReturn(True, self.__executor_return(command.line_num, parameters, method_return_type, statement[1], calling_class_list, interpreter))

            case InterpreterBase.SET_DEF:
                return_initiated, return_field = self.__executor_set(command.line_num, parameters, method_return_type, statement[1], statement[2], calling_class_list, interpreter)
                return StatementReturn(return_initiated, return_field)

            case InterpreterBase.WHILE_DEF:
                function_return = self.__executor_while(command.line_num, parameters, method_return_type, statement[1], statement[2], calling_class_list, interpreter)
                return StatementReturn(function_return[0], function_return[1])

            case InterpreterBase.NEW_DEF:
                new_object_def = self.__executor_new(command.line_num, parameters, statement[1], interpreter)
                return StatementReturn(False, new_object_def)

            case "+" | "-" | "*" | "/" | "%":
                return_initiated, arithmetic_result = self.__executor_arithmetic(command.line_num, parameters, command, statement[1:], calling_class_list, interpreter)
                return StatementReturn(return_initiated, arithmetic_result)

            case "<" | ">" | "<=" | ">=" | "!=" | "==" | "&" | "|":
                return_initiated, comparison_result = self.__executor_compare(command.line_num, parameters, command, statement[1:], calling_class_list, interpreter)
                return StatementReturn(return_initiated, comparison_result)

            case "!":
                return_initiated, notted_boolean = self.__executor_unary_not(command.line_num, parameters, statement[1], calling_class_list, interpreter)
                return StatementReturn(return_initiated, notted_boolean)

            # In format [1] all declared vars (list), [2...] substatements
            case InterpreterBase.LET_DEF:
                declared_vars = statement[1]
                substatements = statement[2:]

                return_initiated, return_field = self.__executor_let(command.line_num, parameters, method_return_type, declared_vars, substatements, calling_class_list, interpreter)
                return StatementReturn(return_initiated, return_field)
            
            # In format [1] statement to try, [2] statement for catch
            case InterpreterBase.TRY_DEF:
                try_statement = statement[1]
                catch_statement = statement[2] if (len(statement) >= 3) else None

                return_initiated, return_field = self.__executor_try(command.line_num, parameters, method_return_type, try_statement, catch_statement, calling_class_list, interpreter)
                return StatementReturn(return_initiated, return_field)

            # In format [1] thing to throw
            case InterpreterBase.THROW_DEF:
                exception_msg = statement[1]

                thrown_exception_field = self.__executor_throw(command.line_num, parameters, method_return_type, exception_msg, calling_class_list, interpreter)
                return StatementReturn(True, thrown_exception_field)

            case _:
                interpreter.error(ErrorType.SYNTAX_ERROR, f"Unknown statement/expression: {command}", command.line_num)

    def __executor_begin(
        self, 
        line_num: int,
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        substatements: List[str], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        statement_return = None
        for substatement in substatements:
            statement_return = self.__run_statement(method_params, method_return_type, substatement, calling_class_list, interpreter)
            if statement_return.return_initiated:
                return (True, statement_return.return_field)
        
        return (False, statement_return.return_field)

    def __executor_call(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        target_obj: str, 
        method_name: str, 
        method_args: List[str], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        # Helper to create modified return value needed to throw exceptions
        def __construct_return(call_return_field: Field):
            if call_return_field is None:
                return (False, call_return_field)
            elif call_return_field.type == Type.EXCEPTION:
                return (True, call_return_field)
            else:
                return (False, call_return_field)
            
        # Evaluate anything in args
        arg_values = list()
        for arg in method_args:
            evaluated_field = self.__executor_return(line_num, method_params, None, arg, calling_class_list, interpreter)   # Re-use some code, does the same stuff

            # Check for exception
            if evaluated_field.type == Type.EXCEPTION:
                return (True, evaluated_field)
            else:
                arg_values.append(evaluated_field)


        other_obj: ObjectDefinition = None

        # Target object may be an expression
        if isinstance(target_obj, list):
            return_field = self.__executor_return(line_num, method_params, None, target_obj, calling_class_list, interpreter)
            # Check for exception
            if return_field.type == Type.EXCEPTION:
                return (True, return_field)
            elif not isinstance(return_field.value, ObjectDefinition):
                interpreter.error(ErrorType.TYPE_ERROR, f"Expression does not return a class", line_num)
            else:
                other_obj = return_field.value
        # Target object is a variable or "me"
        else:
            # Call a method in my own object
            if target_obj == InterpreterBase.ME_DEF:
                # Find lowest derived "ME"
                object_to_call: ObjectDefinition = None
                for o in calling_class_list:
                    if o.inherits(self.class_name):
                        object_to_call = o
                        break
                return __construct_return(object_to_call.call_method(method_name, arg_values, calling_class_list, interpreter))
            if target_obj == InterpreterBase.SUPER_DEF:
                if self.superclass is None:
                    interpreter.error(ErrorType.TYPE_ERROR, f"Super class does not exist on class {self.class_name}", line_num)
                else:
                    return __construct_return(self.superclass.call_method(method_name, arg_values, calling_class_list, interpreter))
            
            # Call a method in another object
            # Check to see if reference is valid
            if (other_obj_field := self.__get_var_from_params_list(target_obj, method_params)) is not None:
                other_obj = other_obj_field.value
            elif (other_obj_field := self.get_var_from_polymorphic_fields(target_obj)) is not None:
                other_obj = other_obj_field.value
            else:
                interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {target_obj}", line_num)

            # Check to see if reference is null
            if other_obj is None:
                interpreter.error(ErrorType.FAULT_ERROR, f"Reference is null: {target_obj}", line_num)

        # Actual function call
        return __construct_return(other_obj.call_method(method_name, arg_values, calling_class_list, interpreter))

    def __executor_if(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        args: List[str], 
        calling_class_list: List[Self],
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
        predicate_return: Field = self.__executor_return(line_num, method_params, None, predicate, calling_class_list, interpreter)
        if predicate_return is None:
            interpreter.error(ErrorType.TYPE_ERROR, f"Predicate cannot return null", line_num)
        # Check for exception
        elif predicate_return.type == Type.EXCEPTION:
            return (True, predicate_return)
        elif predicate_return.type != Type.BOOL:
            interpreter.error(ErrorType.TYPE_ERROR, f"Predicate is not a boolean", line_num)
        else:
            predicate_val: bool = predicate_return.value
        
        # Run the correct clause
        if predicate_val:
            clause_return = self.__run_statement(method_params, method_return_type, true_clause, calling_class_list, interpreter)
            return (clause_return.return_initiated, clause_return.return_field)
        else:
            if false_clause is not None:
                clause_return = self.__run_statement(method_params, method_return_type, false_clause, calling_class_list, interpreter)
                return (clause_return.return_initiated, clause_return.return_field)
            else:
                return (False, None)

    def __executor_input(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        command: str,
        var: str, 
        interpreter: InterpreterBase
    ) -> Field:
        # Check to see if reference is valid
        read_into_var: Field = None
        if (read_into_field := self.__get_var_from_params_list(var, method_params)) is not None:
            if read_into_field.type not in [Type.INT, Type.STRING]:
                interpreter.error(ErrorType.FAULT_ERROR, f"Cannot read into variable '{var}' of type {read_into_field.type}", line_num)
            else:
                read_into_var = read_into_field
        elif (read_into_field := self.get_var_from_polymorphic_fields(var)) is not None:
            read_into_var = read_into_field
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var}", line_num)

        # Read input
        user_input = interpreter.get_input()

        # Type check
        if read_into_var.type == Type.INT:
            if command == "inputs":
                interpreter.error(ErrorType.TYPE_ERROR, f"Incompatible type: Cannot read Type.STRING into Type.INT", line_num)
            
            try:
                int_val = int(user_input)
            except Exception as e:
                interpreter.error(ErrorType.TYPE_ERROR, f"Could not convert input to Type.INT", line_num)

            read_into_field.value = int_val
        else:   # Type.STRING
            if command == "inputi":
                interpreter.error(ErrorType.TYPE_ERROR, f"Incompatible type: Cannot read Type.INT into Type.STRING", line_num)

            read_into_field.value = user_input

        return Field("temp", read_into_var.type, read_into_var.value)

    def __executor_print(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]],
        method_return_type: Tuple[Type, str | None], 
        stuff_to_print: List[str], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
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
                statement_return = self.__run_statement(method_params, method_return_type, expression, calling_class_list, interpreter)
                # Check for exception
                if statement_return.return_field.type == Type.EXCEPTION:
                    return (True, statement_return.return_field)
                else:
                    about_to_print.append(__stringify(statement_return.return_field))
            # Evaluate constant/literal or variable lookup
            else:
                raw_type, raw_thing = utils.parse_type_value(expression)

                append_this = None
                if raw_type is not None:
                    append_this = Field("temp", raw_type, raw_thing)
                else:
                    append_this = self.__get_var_value(line_num, expression, method_params, calling_class_list, interpreter)

                about_to_print.append(__stringify(append_this))      

        final_string = "".join(map(str, about_to_print))
        interpreter.output(final_string)

        return (False, None)

    def __executor_return(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        expr: str, 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Field:
        # A void method should not return anything
        if method_return_type is not None and method_return_type[0] == Type.NULL:
            if expr is not None:
                interpreter.error(ErrorType.TYPE_ERROR, "Invalid return type: void method cannot return anything", line_num)

        # Evaluate the expr expression, if applicable
        if isinstance(expr, list):
            statement_return = self.__run_statement(method_params, method_return_type, expr, calling_class_list, interpreter)
            ret_field = statement_return.return_field
            if ret_field.type == Type.EXCEPTION:
                return ret_field

            # If this is None, then __executor_return was just called to evaluate an expression
            if method_return_type is None:
                return ret_field

            # Actual return statement of method
            # Type check
            try:
                utils.check_compatible_types(Field("ret_type", method_return_type[0], None, method_return_type[1]), ret_field, interpreter)
            except Exception as e:
                interpreter.error(ErrorType.TYPE_ERROR, f"Invalid return type: {str(e)}", line_num)

            return ret_field

        # Not an expression, can be constant/literal or variable name
        else:
            raw_type, raw_value = utils.parse_type_value(expr)

            var_value: Field = None
            # Constant or literal
            if raw_type is not None:
                var_value = Field("temp", raw_type, raw_value)
            # A variable lookup
            else:
                var_name = expr
                var_value = self.__get_var_value(line_num, var_name, method_params, calling_class_list, interpreter)

            # If this is None, then __executor_return was just called to evaluate an expression
            if method_return_type is None:
                return var_value

            # Actual return statement of method
            # Type check
            try:
                utils.check_compatible_types(Field("ret_type", method_return_type[0], None, method_return_type[1]), var_value, interpreter)
            except Exception as e:
                interpreter.error(ErrorType.TYPE_ERROR, f"Invalid return type: {str(e)}", line_num)

            return var_value
            

    def __executor_set(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        var_name: str, 
        new_val: any, 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        # Evaluate the new_val expression, if applicable
        set_to_this = (None, None)
        if isinstance(new_val, list):
            statement_return = self.__run_statement(method_params, method_return_type, new_val, calling_class_list, interpreter)
            if statement_return.return_field is None:
                interpreter.error(ErrorType.TYPE_ERROR, f"Cannot set variable to result of void function", line_num)
            elif statement_return.return_field.type == Type.EXCEPTION:
                return (True, statement_return.return_field)
            else:
                set_to_this = (statement_return.return_field.type, statement_return.return_field.value, statement_return.return_field.obj_name)
        # Get the constant/literal or variable
        else:
            lit_val = utils.parse_type_value(new_val)
            set_to_this = (lit_val[0], lit_val[1], None)

            # set_to_this refers to a variable
            if set_to_this[0] is None:
                # First try to find the variable in the method params (shadowing)
                if (var_field := self.__get_var_from_params_list(new_val, method_params)) is not None:
                    set_to_this = (var_field.type, var_field.value, var_field.obj_name)
                # If not there, try finding it in the class fields
                elif (var_field := self.get_var_from_polymorphic_fields(new_val)) is not None:
                    set_to_this = (var_field.type, var_field.value, var_field.obj_name)
                # If nowhere, return an error
                else:
                    interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {new_val}", line_num)

        field_to_be_set: Field = None
        # First try to find the variable in the method params (shadowing)
        if (found_var := self.__get_var_from_params_list(var_name, method_params)) is not None:
            field_to_be_set = found_var
        # If not there, try finding it in the class fields
        elif (found_var := self.get_var_from_polymorphic_fields(var_name)) is not None:
            field_to_be_set = found_var
        # If nowhere, return an error
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}", line_num)

        # If the field to be set is a template class
        if field_to_be_set.type == Type.TCLASS:
            field_to_be_set.type = Type.OBJ

        # Check compatible types
        try:
            utils.check_compatible_types(field_to_be_set, Field("temp", set_to_this[0], set_to_this[1], set_to_this[2]), interpreter)
        except Exception as e:
            interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type for variable '{var_name}': {str(e)}", line_num)

        # Set values
        field_to_be_set.type = set_to_this[0]
        field_to_be_set.value = set_to_this[1]
        # field_to_be_set.obj_name = set_to_this[2]

        return (False, None)

    def __executor_while(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        predicate: str | List[str], 
        true_clause: List[str], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        if predicate is None or true_clause is None:
            interpreter.error(ErrorType.SYNTAX_ERROR, "Too few or too many arguments for if statement", line_num)

        # Evaluate predicate
        def __evaluate_predicate() -> Tuple[bool, Field]:
            predicate_return: Field = self.__executor_return(line_num, method_params, None, predicate, calling_class_list, interpreter)

            # Check for exception
            if predicate_return.type == Type.EXCEPTION:
                return (False, predicate_return)
            elif predicate_return.type != Type.BOOL:
                interpreter.error(ErrorType.TYPE_ERROR, f"Predicate is not a boolean", line_num)
            else:
                return (predicate_return.value, None)

        while (predicate_return := __evaluate_predicate())[0]:
            clause_return = self.__run_statement(method_params, method_return_type, true_clause, calling_class_list, interpreter)
            if clause_return.return_initiated:
                return (clause_return.return_initiated, clause_return.return_field)
        else:
            # If "predicate_return.value" is False, two options
            # Option 1: the predicate evaluates to False. In this case, the [1] of the tuple will always be None
            #   It is safe to return normally
            if predicate_return[1] is None:
                return (False, None)
            # Option 2: An error occurred. Then the [1] of the tuple will not be None (it will be a Field)
            #   Treat as exception
            else:
                return (True, predicate_return[1])
            

    def __executor_new(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        arg: str, 
        interpreter: any # (Interpreter, but there is a circular dependency so ignore for now)
    ) -> Field:
        # Look for requested class
        other_class = interpreter.get_class(arg)
        other_class_obj: ObjectDefinition = None
        if other_class is None:
            # Check for template class
            if (first_at_sign := arg.find('@')) != -1:
                other_class = interpreter.get_tclass(arg[:first_at_sign])
                if other_class is None:
                    interpreter.error(ErrorType.TYPE_ERROR, f"Unknown class: {arg}", line_num)
                # Create a new object
                else:
                    templated_types = arg[first_at_sign + 1:].split('@')
                    other_class_obj = other_class.instantiate_self_tclass(templated_types, interpreter)
            else:
                interpreter.error(ErrorType.TYPE_ERROR, f"Unknown class: {arg}", line_num)
        else:
            # Create a new object
            other_class_obj = other_class.instantiate_self()

        # Return object as field
        return Field("temp", Type.OBJ, other_class_obj, arg)

    def __executor_arithmetic(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        command: str, 
        args: List[Field],
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        if (len(args) > 2):
            interpreter.error(ErrorType.SYNTAX_ERROR, f"Invalid number of operands for operator: {command}", line_num)

        # Evaluate operands
        arg_values: List[Field] = list()
        for arg in args:
            evaluated_field = self.__executor_return(line_num, method_params, None, arg, calling_class_list, interpreter)   # Re-use some code, does the same stuff

            # Check for exception
            if evaluated_field.type == Type.EXCEPTION:
                return (True, evaluated_field)
            else:
                arg_values.append(evaluated_field)

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

        return (False, Field("temp", Type.STRING if both_strings else Type.INT, result))

    def __executor_compare(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        command: str, 
        args: List[Field],
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        if (len(args) > 2):
            interpreter.error(ErrorType.SYNTAX_ERROR, f"Invalid number of operands for operator: {command}", line_num)

        # Evaluate operands
        arg_values: List[Field] = list()
        for arg in args:
            evaluated_field = self.__executor_return(line_num, method_params, None, arg, calling_class_list, interpreter)   # Re-use some code, does the same stuff

            # Check for exception
            if evaluated_field.type == Type.EXCEPTION:
                return (True, evaluated_field)
            else:
                arg_values.append(evaluated_field)

        # Operands can either be both strings or both ints
        int_string = [Type.INT, Type.STRING]
        int_string_bool = [Type.INT, Type.STRING, Type.BOOL]
        obj_null = [Type.NULL, Type.OBJ, Type.TCLASS]
        just_bool = [Type.BOOL]

        if command in ["<", ">", "<=", ">="] and \
            arg_values[0].type == arg_values[1].type and \
            arg_values[0].type in int_string and \
            arg_values[1].type in int_string:

            pass
        elif command in ["==", "!="] and \
            arg_values[0].type == arg_values[1].type and \
            arg_values[0].type in int_string_bool and \
            arg_values[1].type in int_string_bool:

            pass
        elif command in ["==", "!="] and \
            arg_values[0].type in obj_null and \
            arg_values[1].type in obj_null: 

            # If either object reference is a literal "null", allowed, so need not check for same type
            if arg_values[0].type == Type.NULL or arg_values[1].type == Type.NULL:
                pass
            # Else comparisons need to check for compatibility
            else:
                try:
                    utils.check_compatible_types(arg_values[0], arg_values[1], interpreter)
                except Exception as e:
                    try:
                        utils.check_compatible_types(arg_values[1], arg_values[0], interpreter)
                    except Exception as e:
                        # Only error if both ways are incompatible
                        interpreter.error(ErrorType.TYPE_ERROR, f"Invalid type for operand '{arg_values[1].name}': {str(e)}")
        elif command in ["&", "|"] and \
            arg_values[0].type == arg_values[1].type and \
            arg_values[0].type in just_bool and \
            arg_values[1].type in just_bool:

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

        return (False, Field("temp", Type.BOOL, result))

    def __executor_unary_not(
        self,  
        line_num: int,
        method_params: List[Dict[str, Field]], 
        arg: str, 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        arg_value = self.__executor_return(line_num, method_params, None, arg, calling_class_list, interpreter)
        # Check for exception
        if arg_value.type == Type.EXCEPTION:
            return (True, arg_value)

        # Unary NOT only works on booleans
        if arg_value.type != Type.BOOL:
            interpreter.error(ErrorType.TYPE_ERROR, f"The operator '!' is not compatible with the type of variable '{arg}': {arg_value.type}", line_num)
        else:
            return (False, Field("temp", Type.BOOL, not arg_value.value))

    def __executor_let(
        self, 
        line_num: int,
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None],
        declared_vars: List[str],
        substatements: List[str], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        # Get all declared variables
        declared_fields: Dict[Field] = dict()
        for dec_var in declared_vars:
            field_type = dec_var[0]
            field_name = dec_var[1]
            init_value = dec_var[2] if (len(dec_var) >= 3) else None

            if field_name in declared_fields: # or self.get_var_from_polymorphic_fields(field_name) is not None:
                interpreter.error(ErrorType.NAME_ERROR, f"Duplicate field: {field_name}", line_num)
            else:
                # Initial value not provided, use default value
                if init_value is None:
                    parsed_type = utils.parse_type_from_str(field_type, interpreter.get_valid_class_list(), interpreter.get_valid_template_class_list())
                    if parsed_type is None or parsed_type == Type.NULL:
                        interpreter.error(ErrorType.TYPE_ERROR, f"Undeclared class '{field_type}'", line_num)

                    # If TCLASS, check if number of parameterized types is correct
                    if parsed_type == Type.TCLASS:
                        necessary_ptypes = interpreter.get_tclass(field_type.split('@')[0]).get_number_of_parameterized_types()
                        actual_ptypes = len(field_type.split('@')) - 1

                        if necessary_ptypes != actual_ptypes:
                            interpreter.error(ErrorType.TYPE_ERROR, f"Incorrect number of parameterized types: Expected {necessary_ptypes} but got {actual_ptypes}")

                    # Set field as usual
                    default_init_value = utils.get_default_value(parsed_type)
                    self.fields[field_name] = Field(field_name, parsed_type, default_init_value, (field_type if parsed_type == Type.OBJ or parsed_type == Type.TCLASS else None))
                # Initial value provided
                else:
                    parsed_type, parsed_value = utils.parse_value_given_type(field_type, init_value, self.__names_of_valid_classes, self.__names_of_valid_tclasses)

                    # parsed_type will be none if an error occurred during value parsing (only possible error is incompatible type)
                    if parsed_type is None:
                        interpreter.error(ErrorType.TYPE_ERROR, f"Incompatible type '{field_type}' with value '{init_value}'", line_num)
                    elif parsed_type == Type.NULL:
                        interpreter.error(ErrorType.TYPE_ERROR, f"Undeclared class '{field_type if parsed_value is None else parsed_value}'", line_num)
                    elif parsed_type == Type.OBJ:
                        declared_fields[field_name] = Field(field_name, parsed_type, None, parsed_value)    # last member of "Field" only used for object names
                    elif parsed_type == Type.TCLASS:
                        # Check if number of parameterized types is correct
                        necessary_ptypes = interpreter.get_tclass(parsed_value.split('@')[0]).get_number_of_parameterized_types()
                        actual_ptypes = len(field_type.split('@')) - 1

                        if necessary_ptypes != actual_ptypes:
                            interpreter.error(ErrorType.TYPE_ERROR, f"Incorrect number of parameterized types: Expected {necessary_ptypes} but got {actual_ptypes}")

                        declared_fields[field_name] = Field(field_name, parsed_type, None, parsed_value)
                    else:
                        declared_fields[field_name] = Field(field_name, parsed_type, parsed_value)

        # Add declared fields to FRONT of method params for precedence
        new_method_params = [declared_fields] + method_params

        # Everything else is just like running a begin statement
        return self.__executor_begin(line_num, new_method_params, method_return_type, substatements, calling_class_list, interpreter)

    def __executor_throw(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None], 
        exception_msg: str, 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Field:
        # Evaluate expression
        if isinstance(exception_msg, list):
            statement_return = self.__run_statement(method_params, method_return_type, exception_msg, calling_class_list, interpreter)
            if statement_return.return_field.type != Type.STRING and statement_return.return_field.type != Type.EXCEPTION:
                interpreter.error(ErrorType.TYPE_ERROR, f"Cannot throw object of type '{statement_return.return_field.type}', expected 'Type.STRING'")

            return Field("temp", Type.EXCEPTION, statement_return.return_field.value, None)
        # Evaluate constant/literal or variable lookup
        else:
            raw_type, raw_thing = utils.parse_type_value(exception_msg)
            if raw_type is not None:
                if raw_type != Type.STRING and raw_type != Type.EXCEPTION:
                    interpreter.error(ErrorType.TYPE_ERROR, f"Cannot throw object of type '{raw_type}', expected 'Type.STRING'")

                return Field("temp", Type.EXCEPTION, raw_thing, None)
            else:
                found_field = self.__get_var_value(line_num, exception_msg, method_params, calling_class_list, interpreter)
                if found_field.type != Type.STRING and found_field.type != Type.EXCEPTION:
                    interpreter.error(ErrorType.TYPE_ERROR, f"Cannot throw object of type '{found_field.type}', expected 'Type.STRING'")
                
                return Field("temp", Type.EXCEPTION, found_field.value, None)
            
    def __executor_try(
        self,
        line_num: int, 
        method_params: List[Dict[str, Field]], 
        method_return_type: Tuple[Type, str | None], 
        try_statement: str, 
        catch_statement: str, 
        calling_class_list: List[Self], 
        interpreter: InterpreterBase
    ) -> Tuple[bool, Field]:
        # Run try statement
        try_return = self.__run_statement(method_params, method_return_type, try_statement, calling_class_list, interpreter)

        # If no exception occurs, proceed normally
        if try_return.return_field is None or try_return.return_field.type != Type.EXCEPTION:
            return (try_return.return_initiated, try_return.return_field)
        # Else try to run the catch block
        else:
            if catch_statement is not None:
                # Add a local var 'exception' that contains the thrown message
                modified_method_params = [{'exception': Field("exception", Type.STRING, try_return.return_field.value, None)}]  + method_params
                catch_return = self.__run_statement(modified_method_params, method_return_type, catch_statement, calling_class_list, interpreter)
                return (catch_return.return_initiated, catch_return.return_field)
            # No catch block, propagate exception
            else:
                return (try_return.return_initiated, try_return.return_field)

    def __get_var_value(
        self,  
        line_num: int,
        var_name: str, 
        method_params: List[Dict[str, Field]], 
        calling_class_list: List[Self],
        interpreter: InterpreterBase
    ) -> Field:
        # Reference to self
        if var_name == InterpreterBase.ME_DEF:
            # Find lowest derived "ME"
            lowest_me: ObjectDefinition = None
            for o in calling_class_list:
                if o.inherits(self.class_name):
                    lowest_me = o
                    break
            return Field("temp", Type.OBJ, lowest_me, lowest_me.class_name)
        # A variable lookup
        elif (found_var := self.__get_var_from_params_list(var_name, method_params)) is not None:
            return found_var
        # If not there, try finding it in the class fields
        elif (found_var := self.get_var_from_polymorphic_fields(var_name)) is not None:
            return found_var
        # If nowhere, return an error
        else:
            interpreter.error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}", line_num)

    # Looks through params list for variable
    # Each let block adds their own params dic to the front of the list
    # Use the first instance of the defined variable
    def __get_var_from_params_list(self, var_name: str, method_params: List[Dict[str, Field]]) -> Field | None:
        for dic in method_params:
            if str(var_name) in dic:
                return dic[str(var_name)]
        return None