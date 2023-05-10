from interpreterv2 import Interpreter

program = [
    '(class person',
        '(field person hey null)',
    ')',
    '(class main',
        '(method int add ((int a) (int b))',
            '(return (+ a b))',
        ')',
        '(method void main ()',
            '(print "yay!")',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
