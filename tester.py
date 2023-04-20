from interpreterv1 import Interpreter

program = ['(class main',
                '(field x 0)',

                '(method hello_world () (print “hello world!”))', 
                '(method main ()',
                    '(begin',
                        '(set x (begin (return "string literal")))',
                    ')',
                ')',
            ')',
            '(class main2',
                '(method hello_world () (print “hello world!”))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
