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
                        '(set n (new main2))',
                        '(print (== null n))',
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
            '(class p',
                '(method hello_world () (print "hello world!"))', 
                '(method main () (call me hello_world))',
            ')',
            '(class p',
                '(method hello_world () (print "hello world!"))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
