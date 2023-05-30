from interpreterv3 import Interpreter

program = []
with open('tests/long_except.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
