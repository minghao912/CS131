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
        '(method int fake_method ()',
            '(return)',
        ')',
        '(method void main ()',
            '(let ((int local_x 10) (string local_str "string"))',
                '(print local_x " " local_str " " test_var)',
            ')',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
