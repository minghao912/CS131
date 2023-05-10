from interpreterv1 import Interpreter

program = [
    '(class main',
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
                '(set c (call me test x))',
                '(call me hello_world)',
            ')',
        ')',
        '(method test (arg)',
            '(return (/ x 6))',
        ')'
    ')',
    '(class p',
        '(method hello_world () (print "hello world!"))', 
        '(method main () (call me hello_world))',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
