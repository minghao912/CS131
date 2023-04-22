from interpreterv1 import Interpreter

program = ['(class main',
                '(field x 7)',
                '(field n null)',
                '(field b true)',

                '(method hello_world ()',
                    '(print "hello world! the result of function call is: " (call me test x) ", also field n is " n ", and the boolean is " b)',
                ')', 
                '(method main ()',
                    '(begin',
                        '(set x 5)',
                        '(set b (! b))',
                        '(call me hello_world)',
                    ')',
                ')',
                '(method test (arg)',
                    '(return (| false true))'
                ')'
            ')',
            '(class main2',
                '(method hello_world () (print “hello world!”))', 
                '(method main () (call me hello_world))',
            ')']

interpreter = Interpreter()
interpreter.run(program)
