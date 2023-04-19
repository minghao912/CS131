from interpreterv1 import Interpreter

program = ['(class main',
                '(method hello_world () (print “hello world!”))', 
                '(method main () (begin (call me hello_world)))',
            ')',
            '(class main2',
                '(method hello_world () (print “hello world!”))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
