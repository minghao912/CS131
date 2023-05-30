from interpreterv3 import Interpreter

program = []
with open('tests/throw_nested_if.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
