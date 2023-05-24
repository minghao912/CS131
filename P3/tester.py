from interpreterv3 import Interpreter

program = []
with open('tests/test_except13.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
