from interpreterv3 import Interpreter

program = []
with open('tests/template_local_var.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
