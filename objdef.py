from intbase import InterpreterBase
from helperclasses import Field, Method

from typing import Callable, Dict, List

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

        if not methodBody[0] == InterpreterBase.BEGIN_DEF:
            self.__run_statement(matched_parameters, methodBody)
        else:
            for statement in methodBody:
                self.__run_statement(matched_parameters, statement)

    def __run_statement(self, parameters: Dict[str, any], statement: List[str]):
        if statement == "begin":
            return

        print(f"Passed parameters: {parameters}")
        print(f"Statement to execute: {statement}")