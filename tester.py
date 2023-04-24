from interpreterv1 import Interpreter

program = ['(class main',
                '(field x 7)',
                '(field n null)',
                '(field b true)',
                '(field c null)',

                '(method hello_world ()',
                    '(print "hello world! the result of function call is: " c ", also field n is " n ", and the boolean is " b)',
                ')', 
                '(method main ()',
                    '(begin',
                        '(call me test (+ x 1))',
                    ')',
                ')',
                '(method test (arg)',
                    '(if (== 0 (% arg 2))',
                        '(print "x is even")',
                        '(print "x is odd")',
                    ')',
                ')'
            ')',
            '(class main2',
                '(method hello_world () (print "hello world!"))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
