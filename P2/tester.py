from interpreterv2 import Interpreter

program = []
with open('tests/downcast2.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
