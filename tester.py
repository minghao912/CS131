from interpreterv1 import Interpreter

program = ['(class main', 
                '(method hello_world () (print “hello world!”))', 
            ')']

interpreter = Interpreter()
interpreter.run(program)
