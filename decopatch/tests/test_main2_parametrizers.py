import pytest

from decopatch import FirstArgDisambiguation, DECORATED
from pytest_cases import case_name

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


def foo():
    pass


def goo():
    pass


def is_foo_or_goo(arg):
    if arg in {foo, goo}:
        return FirstArgDisambiguation.is_positional_arg
    else:
        return FirstArgDisambiguation.is_decorated_target


DEFAULT_DUMMY_VALUE = 12


@case_name("@replace_by_foo")
def case_no_parenthesis(replace_by_foo, name):
    """ Tests the decorator in a no-parenthesis way @my_decorator """

    return eval(name[1:]), foo


@case_name("@replace_by_foo()")
def case_empty_parenthesis(replace_by_foo, name):
    """ Tests the decorator in a with-empty-parenthesis way @my_decorator() """

    return eval(name[1:]), foo


@case_name("@replace_by_foo(goo)")
def case_one_arg_positional_callable(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(goo) """

    return eval(name[1:]), goo


@case_name("@replace_by_foo('hello')")
def case_one_arg_positional_noncallable(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator("hello") """

    return eval(name[1:]), foo


@case_name("@replace_by_foo(DEFAULT_DUMMY_VALUE)")
def case_one_arg_positional_noncallable_default(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(DEFAULT_DUMMY_VALUE) """

    return eval(name[1:]), foo


@case_name("@replace_by_foo(replacement=goo)")
def case_one_kwarg_callable(replace_by_foo, name):
    """ Tests the decorator with one kw argument @my_decorator(replacement=goo) """

    return eval(name[1:]), goo


@case_name("@replace_by_foo(dummy='hello')")
def case_one_kwarg_noncallable(replace_by_foo, name):
    """ Tests the decorator with one kw argument @my_decorator(dummy="hello") """

    return eval(name[1:]), foo


@case_name("@replace_by_foo(dummy=DEFAULT_DUMMY_VALUE)")
def case_one_kwarg_noncallable_default(replace_by_foo, name):
    """ Tests the decorator with one kw argument @my_decorator(dummy=DEFAULT_DUMMY_VALUE) """

    return eval(name[1:]), foo


@case_name("@replace_by_foo(goo, 'hello')")
def case_two_args_positional_callable_first(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(goo) """

    return eval(name[1:]), goo


@case_name("@replace_by_foo('hello', goo)")
def case_two_args_positional_callable_last(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(goo) """

    return eval(name[1:]), goo


@case_name("@replace_by_foo(goo, DEFAULT_DUMMY_VALUE)")
def case_two_args_positional_callable_first_dummy_default(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(goo) """

    return eval(name[1:]), goo


@case_name("@replace_by_foo(DEFAULT_DUMMY_VALUE, goo)")
def case_two_args_positional_callable_last_dummy_default(replace_by_foo, name):
    """ Tests the decorator with one positional argument @my_decorator(goo) """

    return eval(name[1:]), goo



# @pytest.mark.parametrize('new_val_for_dummy', ['hello', DEFAULT_DUMMY_VALUE])
# def case_two_args_kw_both_orders(case_data, new_val_for_dummy):
#     """ Tests the decorator in a with-empty-parenthesis way @my_decorator() """
#
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     help(replace_by_foo)
#     print(args_info)
#
#     # why would this test fail ?
#     expected_failure_msg = None
#     if not args_info.has_dummy_kwarg:
#         expected_failure_msg = "'dummy' kw arg is not present in the signature"
#         expected_err_type = TypeError
#     elif not args_info.has_replacement_kwarg:
#         expected_failure_msg = "'replacement' kw arg is not present in the signature"
#         expected_err_type = TypeError
#     elif new_val_for_dummy is DEFAULT_DUMMY_VALUE \
#             and args_info.first_arg_name == "replacement" and not is_first_arg_protected:
#         # note: is new_val_for_dummy is DEFAULT_DUMMY_VALUE, then the stack will not be able to know that 2 arguments
#         # were provided.
#         expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#         expected_err_type = AmbiguousFirstArgumentTypeError
#
#     if expected_failure_msg is None:
#         print("this is supposed to work")
#
#         @replace_by_foo(dummy=new_val_for_dummy, replacement=goo)
#         def bar():
#             pass
#
#         assert bar is goo
#
#         @replace_by_foo(replacement=goo, dummy=new_val_for_dummy)
#         def bar():
#             pass
#
#         assert bar is goo
#
#     else:
#         print("this is supposed to raise a '%s' because %s" % (expected_err_type, expected_failure_msg))
#
#         with pytest.raises(expected_err_type):
#             @replace_by_foo(dummy=new_val_for_dummy, replacement=goo)
#             def bar():
#                 pass
#
#         with pytest.raises(expected_err_type):
#             @replace_by_foo(replacement=goo, dummy=new_val_for_dummy)
#             def bar():
#                 pass


# class ArgsDetails:
#     def __init__(self, nb_mandatory_args, nb_optional_args, nb_positional_args,
#                  first_arg_name, has_dummy_kwarg, has_replacement_kwarg):
#         self.nb_mandatory_args = nb_mandatory_args
#         self.nb_optional_args = nb_optional_args
#         self.nb_positional_args = nb_positional_args
#         self.nb_args = nb_optional_args + nb_mandatory_args
#         self.first_arg_name = first_arg_name
#         self.has_dummy_kwarg = has_dummy_kwarg
#         self.has_replacement_kwarg = has_replacement_kwarg
#
#     def __str__(self):
#         return "nb args: %s ; " \
#                "nb mandatory: %s ; " \
#                "nb optional: %s ; " \
#                "nb positional: %s ; " \
#                "has dummy kwarg: %s ; " \
#                "has replacement kwarg: %s" \
#                "" % (self.nb_args,
#                      self.nb_mandatory_args,
#                      self.nb_optional_args,
#                      self.nb_positional_args,
#                      self.has_dummy_kwarg,
#                      self.has_replacement_kwarg)
#
#
# def get_args_info(function):
#     """
#     Returns the nb of arguments of each type in the function's signature.
#     Skips any arg with default value of DECORATED automatically
#
#     :param function:
#     :return:
#     """
#     s = signature(function)
#
#     params_to_check = [p for p in s.parameters.values() if p.default is not DECORATED]
#
#     nb_args = len(params_to_check)
#     nb_mandatory_args = len([p for p in params_to_check if p.default is p.empty])
#
#     # nb optional args
#     nb_optional_args = nb_args - nb_mandatory_args
#
#     first_arg_name = params_to_check[0].name if len(params_to_check) > 0 else None
#
#     has_dummy_kwarg = len([p for p in params_to_check if p.name == 'dummy']) > 0
#     has_replacement_kwarg = len([p for p in params_to_check if p.name == 'replacement']) > 0
#
#     # nb positional args
#     nb_positional_args = 0
#     for p in params_to_check:
#         if p.kind is Parameter.VAR_POSITIONAL:
#             nb_positional_args = 1000
#             break
#         elif p.kind in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}:
#             nb_positional_args += 1
#
#     return ArgsDetails(nb_mandatory_args=nb_mandatory_args, nb_optional_args=nb_optional_args,
#                        nb_positional_args=nb_positional_args,
#                        first_arg_name=first_arg_name,
#                        has_dummy_kwarg=has_dummy_kwarg,
#                        has_replacement_kwarg=has_replacement_kwarg)
