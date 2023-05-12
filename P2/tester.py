from interpreterv2 import Interpreter

program = [
    '(class person',
        '(field string name "")',
        '(method void set_name ((string new_name))',
            '(set name new_name)',
        ')',
        '(method string get_name ()',
            '(return name)',
        ')',
        '(method person get_self ()',
            '(return me)',
        ')',
    ')',
    '(class student inherits person',
        '(field string major "")',
        '(method void set_major ((string new_major))',
            '(set major new_major)',
        ')',
        '(method string get_major ()',
            '(return major)',
        ')',
    ')',
    '(class main',
        '(field int test_var 5)',
        '(field person test_person null)',
        '(field student test_student null)',

        '(method void main ()',
            '(begin',
                '(set test_person (new person))',
                '(set test_student (new student))',

                '(call test_person set_name "Barbara")',

                '(call test_student set_name "Yuki")',
                '(call test_student set_major "Marine Biology")',

                '(print (call test_person get_name))',
                '(print (call test_student get_name) " majors in " (call test_student get_major))',
            ')',
        ')',
    ')'
]

program_ll = [
    '(class LinkedList',
        '(field int value 0)',
        '(field LinkedList next null)',

        '(method int get_value ()',
            '(return value)',
        ')',
        '(method void set_value ((int new_value))',
            '(set value new_value)',
        ')',
        '(method LinkedList get_next ()',
            '(return next)',
        ')',
        '(method void set_next ((LinkedList new_next))',
            '(set next new_next)',
        ')',
    ')',

    '(class main',
        '(field LinkedList ll null)',

        '(method LinkedList create_ll ((int one) (int two) (int three))',
            '(let ((LinkedList ll_1 null) (LinkedList ll_2 null) (LinkedList ll_3 null))',
                '(set ll_1 (new LinkedList))',
                '(set ll_2 (new LinkedList))',
                '(set ll_3 (new LinkedList))',

                '(call ll_1 set_value one)',
                '(call ll_2 set_value two)',
                '(call ll_3 set_value three)',

                '(call ll_1 set_next ll_2)',
                '(call ll_2 set_next ll_3)',

                '(return ll_1)',
            ')',
        ')',

        '(method void main ()',
            '(let ((LinkedList cur_node null))',
                '(set ll (call me create_ll 1 2 3))',

                '(set cur_node ll)',
                '(while (!= cur_node null)',
                    '(begin',
                        '(print (call cur_node get_value))',
                        '(set cur_node (call cur_node get_next))',
                    ')',
                ')',
            ')',
        ')',
    ')'
]

interpreter = Interpreter()
interpreter.run(program)
