from interpreterv3 import Interpreter

program = []
with open('tests/test_template1.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
