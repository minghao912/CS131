from interpreterv1 import Interpreter

program = ['(class main',
                '(field x 7)',
                '(field n null)',

                '(method hello_world ()',
                    '(print "hello world! the result of function call is: " (call me test x) ", also field n is " n ", and this boolean is " true)',
                ')', 
                '(method main ()',
                    '(begin',
                        '(set x (call me test x))',
                        '(call me hello_world)',
                    ')',
                ')',
                '(method test (arg)',
                    '(return arg)'
                ')'
            ')',
            '(class main2',
                '(method hello_world () (print “hello world!”))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
