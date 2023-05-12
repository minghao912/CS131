from intbase import ErrorType, InterpreterBase 
from bparser import BParser
from classdef import ClassDefinition

from typing import Dict, List

# Brewin v2 interpreter
class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

        # Instance vars
        self.__classes: Dict[str, ClassDefinition] = dict()
        self.trace_output = trace_output

    def run(self, program: List[str]):
        # Parse program
        result, parsed_program = BParser.parse(program)
        if not result:
            return

        # Discover all classes and put into storage
        for top_level_chunk in parsed_program:
            # top_level_chunk[0]: class, [1]: class_name, [2]: class_contents

            # Ignore if not a class definition
            if not top_level_chunk[0] == InterpreterBase.CLASS_DEF:
                continue

            # Create that class and add it to storage
            new_class_name = top_level_chunk[1]
            if new_class_name in self.__classes:
                self.error(ErrorType.NAME_ERROR, f"Duplicate class name {new_class_name}", new_class_name.line_num)
            else:
                current_class_list = list(self.__classes.keys()) + [str(new_class_name)]
                self.__classes[new_class_name] = ClassDefinition(top_level_chunk, current_class_list, self, self.trace_output)

        # Find main class
        if "main" not in self.__classes:
            self.error(ErrorType.NAME_ERROR, "No main class found")

        # Instantiate and run main class
        main_class = self.__classes['main'].instantiate_self()
        main_class.call_method('main', [], self)

        # DEBUG
        if self.trace_output:
            print(f"Main.x is: {main_class.fields['x'].value}")

        return

    def get_class(self, class_name: str) -> ClassDefinition | None:
        if class_name not in self.__classes:
            return None
        else:
            return self.__classes[class_name]