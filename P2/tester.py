from interpreterv2 import Interpreter

program = [
    '(class dog',
        '(field int age 5)',
    ')',
    '(class person',
        '(field person hey null)',
        '(field string name "")',
        '(method void set_name ((string new_name))',
            '(set name new_name)',
        ')',
        '(method void print_name ()',
            '(print name)',
        ')',
        '(method person get_self ()',
            '(return me)',
        ')',
    ')',
    '(class main',
        '(field int test_var 5)',
        '(field person test_obj null)',
        '(field person jeff null)',
        '(method int add ((int a) (int b))',
            '(return (+ a b))',
        ')',
        '(method void main ()',
            '(begin',
                '(set test_var 7)',
                '(set test_obj (new person))',
                '(call test_obj set_name "Jeff")',
                '(set jeff (call test_obj get_self))',
                '(call jeff print_name)',
            ')',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
