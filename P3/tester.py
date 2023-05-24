from interpreterv3 import Interpreter

program = []
with open('tests/field_default_val2.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
