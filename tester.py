from interpreterv1 import Interpreter

program = ['(class main',
                '(field x 0)',
                '(field n null)',
                '(field b true)',
                '(field c null)',

                '(method hello_world ()',
                    '(print "hello world! the result of function call is: " c ", also field n is " n ", and the boolean is " b)',
                ')', 
                '(method main ()',
                    '(begin',
                        '(inputi x)',
                        '(print "the user typed in " x)',
                        '(call me test x)',
                    ')',
                ')',
                '(method test (arg)',
                    '(while (> x 0)',
                        '(begin',
                            '(if (< x 6) (return))',
                            '(print "x is " x)',
                            '(set x (- x 1))',
                        ')',
                    ')',
                ')'
            ')',
            '(class main2',
                '(method hello_world () (print "hello world!"))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
