from interpreterv3 import Interpreter

program = []
with open('tests/let_default_val.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
