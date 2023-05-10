from interpreterv2 import Interpreter

program = [
    '(class dog',
        '(field int age 5)',
    ')',
    '(class person',
        '(field person hey null)',
    ')',
    '(class main',
        '(field int test_var 5)',
        '(field person test_obj null)',
        '(method int add ((int a) (int b))',
            '(return (+ a b))',
        ')',
        '(method void main ()',
            '(begin',
                '(set test_var 7)',
                '(set test_obj (new person))',
                '(print "yay! " test_var)',
            ')',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
