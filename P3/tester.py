from interpreterv3 import Interpreter

program = []
with open('tests/template_ex3.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
