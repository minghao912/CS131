from intbase import ErrorType, InterpreterBase 
from bparser import BParser
from classdef import ClassDefinition

from typing import Dict, List

# Brewin v1 interpreter
class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

        # Instance vars
        self.classes: Dict[str, ClassDefinition] = dict()

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
            if top_level_chunk[1] in self.classes:
                self.error(ErrorType.NAME_ERROR, f"Duplicate class name {top_level_chunk[1]}", top_level_chunk[1].line_num)
            else:
                self.classes[top_level_chunk[1]] = ClassDefinition(
                    top_level_chunk, 
                    lambda err_msg, err_line: self.error(ErrorType.NAME_ERROR, err_msg, err_line)
                )

        # Find main class
        if "main" not in self.classes:
            self.error(ErrorType.TYPE_ERROR, "No class named main found")

        # Instantiate and run main class
        main_class = self.classes['main'].instantiate_self()
        main_class.call_method('main', [], lambda method_name: self.error(ErrorType.NAME_ERROR, f"Could not find method {method_name}"))

        return