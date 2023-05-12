from interpreterv2 import Interpreter

program = []
with open('tests/inheritance_example.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
