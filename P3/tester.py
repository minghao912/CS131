from interpreterv3 import Interpreter

program = []
with open('tests/fail_template_name_err.brewin') as f:
    program = f.read().splitlines()
    f.close()

interpreter = Interpreter()
interpreter.run(program)
