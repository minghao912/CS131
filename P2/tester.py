from interpreterv2 import Interpreter

program = [
    '(class person',
        '(field person hey null)',
    ')',
    '(class main',
        #'(method int add ((int a) (int b))',
        #    '(return (+ a b))',
        #')',
        '(field person q null)',
        '(method main ()',
            '(print q)',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
