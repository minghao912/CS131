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

    def call_method(self, methodName: str, parameters: Dict[str, any], error_callback: Callable[[str], None]):
        if not methodName in self.methods:
            error_callback(methodName)

        # See if begin statement or just one
        methodBody = self.methods[methodName].body

        if not methodBody[0] == InterpreterBase.BEGIN_DEF:
            self.__run_statement(parameters, methodBody)
        else:
            for statement in methodBody:
                self.__run_statement(parameters, statement)

    def __run_statement(self, parameters: Dict[str, any], statement: List[str]):
        print(statement)