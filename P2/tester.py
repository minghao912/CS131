from interpreterv2 import Interpreter

program = []
with open('tests/test_polymorphism4.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
