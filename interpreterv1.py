from intbase import InterpreterBase 
from bparser import BParser
from classdef import ClassDefinition

from typing import List

# Brewin v1 interpreter
class Interpreter(InterpreterBase):
    classes = dict()

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

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
            self.classes[top_level_chunk[1]] = ClassDefinition(top_level_chunk)

        # Find main class

        # Instantiate and run main class

        return