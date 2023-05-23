from intbase import ErrorType, InterpreterBase 
from bparser import BParser
from classdef import ClassDefinition

from typing import Dict, List, Set

# Brewin v3 interpreter
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
        discovery_list: Set[str] = set()
        for top_level_chunk in parsed_program:
            # top_level_chunk[0]: class, [1]: class_name, [2]: class_contents

            # Ignore if not a class definition
            if not top_level_chunk[0] == InterpreterBase.CLASS_DEF:
                continue

            # Parse definition
            new_class_name = top_level_chunk[1]
            discovery_list.add(new_class_name)

        # Actually create the classes
        for top_level_chunk in parsed_program:
            # top_level_chunk[0]: class, [1]: class_name, [2]: class_contents

            # Ignore if not a class definition
            if not top_level_chunk[0] == InterpreterBase.CLASS_DEF:
                continue

            # Parse definition
            new_class_name = top_level_chunk[1]
            superclass: ClassDefinition = None
            if len(top_level_chunk) >= 4 and top_level_chunk[2] == InterpreterBase.INHERITS_DEF:
                superclass_name: str = top_level_chunk[3]
                if (superclass_def := self.get_class(superclass_name)) is None:
                    self.error(ErrorType.TYPE_ERROR, f"Invalid class '{superclass_name}' in '{top_level_chunk}'", new_class_name.line_num)
                else:
                    superclass = superclass_def

            # Create that class and add it to storage
            if new_class_name in self.__classes:
                self.error(ErrorType.TYPE_ERROR, f"Duplicate class name {new_class_name}", new_class_name.line_num)
            else:
                # current_class_list = list(self.__classes.keys()) + [str(new_class_name)]
                current_class_list = list(discovery_list)
                self.__classes[new_class_name] = ClassDefinition(top_level_chunk, superclass, current_class_list, self, self.trace_output)

        # Find main class
        if "main" not in self.__classes:
            self.error(ErrorType.NAME_ERROR, "No main class found")

        # Instantiate and run main class
        main_class = self.__classes['main'].instantiate_self()
        main_class.call_method('main', [], [main_class], self)

        # DEBUG
        if self.trace_output:
            print(f"Main.x is: {main_class.fields['x'].value}")

        return

    def get_class(self, class_name: str) -> ClassDefinition | None:
        if class_name not in self.__classes:
            return None
        else:
            return self.__classes[class_name]
        
    def get_valid_class_list(self) -> List[str]:
        return list(self.__classes.keys())