from intbase import InterpreterBase

from typing import List

class ClassDefinition:
    name = ""
    methods = dict()
    fields = dict()

    def __init__(self, chunk: List[str | List[str]]):
        self.name = chunk[1]
        classbody = chunk[2]

        for body_chunk in classbody:
            # Determine whether it's a method or field
            match body_chunk[0]:
                case InterpreterBase.FIELD_DEF:
                    pass
                case InterpreterBase.METHOD_DEF:
                    pass
                