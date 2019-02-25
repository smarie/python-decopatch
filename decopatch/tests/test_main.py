# import pytest
#
# from pytest_cases import cases_data, THIS_MODULE, cases_generator
# from decopatch import decorator, DECORATED, FirstArgDisambiguation, AmbiguousFirstArgumentTypeError, \
#     InvalidMandatoryArgError
#
# try:  # python 3.3+
#     from inspect import signature
# except ImportError:
#     from funcsigs import signature
#
#
# # ---- expected results
# class Details:
#     def __init__(self, nb_mandatory_args, nb_optional_args, first_arg_name, has_dummy_kwarg, has_replacement_kwarg):
#         self.nb_mandatory_args = nb_mandatory_args
#         self.nb_optional_args = nb_optional_args
#         self.nb_args = nb_optional_args + nb_mandatory_args
#         self.first_arg_name = first_arg_name
#         self.has_dummy_kwarg = has_dummy_kwarg
#         self.has_replacement_kwarg = has_replacement_kwarg
#
#     def __str__(self):
#         return "nb args: %s ; nb mandatory: %s ; no optional: %s ; has dummy kwarg: %s ; has replacement kwarg: %s" \
#                "" % (self.nb_args, self.nb_mandatory_args, self.nb_optional_args, self.has_dummy_kwarg, self.has_replacement_kwarg)
# # -------------
#
#
# def foo():
#     pass
#
#
# def goo():
#     pass
#
#
# def is_foo_or_goo(arg):
#     if arg in {foo, goo}:
#         return FirstArgDisambiguation.is_positional_arg
#     else:
#         return FirstArgDisambiguation.is_decorated_target
#
#
# DEFAULT_DUMMY_VALUE = 12
#
#
# @cases_generator("case_allfine_0_args_kwonly={kwonly}", kwonly=[False, True])
# def case_allfine_0_args(kwonly):
#     """
#     This decorator has no arguments and can therefore be used with and without parenthesis
#     """
#
#     # Note: we will decorate it later, otherwise the get_args_info will not be accurate in this particular case
#
#     if kwonly:
#         # @decorator
#         def replace_by_foo(*, f=DECORATED):
#             return foo
#     else:
#         # @decorator
#         def replace_by_foo(f=DECORATED):
#             return foo
#
#     return decorator(replace_by_foo), get_args_info(replace_by_foo), True
#
#
# def case_1_mandatory_0_optional_noncallable_not_protected():
#     """
#     This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis
#     """
#     @decorator
#     def replace_by_foo(dummy, f=DECORATED):
#         return foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), False
#
#
# def case_1_mandatory_0_optional_noncallable_protected():
#     """
#     This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis
#     """
#     @decorator(can_first_arg_be_ambiguous=False)
#     def replace_by_foo(dummy, f=DECORATED):
#         return foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_1_mandatory_0_optional_callable_not_protected():
#     """This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis"""
#     @decorator
#     def replace_by_foo(replacement, f=DECORATED):
#         return replacement
#
#     return replace_by_foo, get_args_info(replace_by_foo), False
#
#
# def case_1_mandatory_0_optional_callable_protected():
#     """This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis"""
#     @decorator(callable_or_cls_firstarg_disambiguator=is_foo_or_goo)
#     def replace_by_foo(replacement, f=DECORATED):
#         return replacement
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_2_mandatory_0_optional_callable_first():
#     @decorator
#     def replace_by_foo(replacement, dummy, f=DECORATED):
#         return replacement
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_2_mandatory_0_optional_callable_last():
#     @decorator
#     def replace_by_foo(dummy, replacement, f=DECORATED):
#         return replacement
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_2_mandatory_0_optional_no_callable():
#     @decorator
#     def replace_by_foo(dummy, dummy2, f=DECORATED):
#         return foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_0_mandatory_2_optional_dummy_first_not_protected():
#     @decorator
#     def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED):
#         return replacement if replacement is not None else foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), False
#
#
# def case_0_mandatory_2_optional_dummy_first_protected():
#     @decorator(callable_or_cls_firstarg_disambiguator=lambda a: FirstArgDisambiguation.is_decorated_target)
#     def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED):
#         return replacement if replacement is not None else foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# def case_0_mandatory_2_optional_replacement_first_not_protected():
#     @decorator
#     def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED):
#         return replacement if replacement is not None else foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), False
#
#
# def case_0_mandatory_2_optional_replacement_first_protected():
#     @decorator(callable_or_cls_firstarg_disambiguator=is_foo_or_goo)
#     def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED):
#         return replacement if replacement is not None else foo
#
#     return replace_by_foo, get_args_info(replace_by_foo), True
#
#
# # -------------------------
#
#
# @cases_data(module=THIS_MODULE)
# def test_correctly_decorated(case_data):
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     assert '__source__' in vars(replace_by_foo)
#
#
# @cases_data(module=THIS_MODULE)
# def test_no_parenthesis(case_data):
#     """ Tests the decorator in a no-parenthesis way @my_decorator """
#
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     help(replace_by_foo)
#     print(args_info)
#
#     # why would this test fail ?
#     expected_failure_msg = None
#     if args_info.nb_mandatory_args > 0:
#         expected_failure_msg = "there are mandatory arguments. By default `decopatch` will assume that they cannot " \
#                                "be callable/class, and will therefore raise an error in this no-parenthesis mode"
#     elif not is_first_arg_protected:
#         expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#
#     # the no-parenthesis mode is only allowed when the function has no mandatory arguments
#     if expected_failure_msg is None:
#         print("This is supposed to work")
#
#         @replace_by_foo
#         def bar():
#             pass
#
#         assert bar is foo
#     else:
#         if args_info.nb_mandatory_args > 1:
#             # python at work
#             expected_err_type = TypeError
#         else:
#             # our stack
#             if not is_first_arg_protected:
#                 expected_err_type = AmbiguousFirstArgumentTypeError
#             else:
#                 expected_err_type = InvalidMandatoryArgError
#
#         print("this is supposed to raise a '%s' because '%s'" % (expected_err_type, expected_failure_msg))
#
#         with pytest.raises(expected_err_type):
#             @replace_by_foo
#             def bar():
#                 pass
#
#
# @cases_data(module=THIS_MODULE)
# def test_empty_parenthesis(case_data):
#     """ Tests the decorator in a with-empty-parenthesis way @my_decorator() """
#
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     help(replace_by_foo)
#     print(args_info)
#
#     # why would this test fail ?
#     expected_failure_msg = None
#     if args_info.nb_mandatory_args > 0:
#         expected_failure_msg = "there are mandatory arguments. This is the normal python exception"
#
#     # WE DO NOT NEED PROTECTION HERE, THIS IS AN EXPLICIT CALL
#     # elif not is_first_arg_protected:
#     #     expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#
#     # the explicit no-args call is only allowed when the function has no mandatory arguments
#     if expected_failure_msg is None:
#         print("This is supposed to work")
#
#         @replace_by_foo()
#         def bar():
#             pass
#
#         assert bar is foo
#     else:
#         print("this is supposed to fail because %s" % expected_failure_msg)
#
#         with pytest.raises(TypeError):
#             @replace_by_foo()
#             def bar():
#                 pass
#
#
# @cases_data(module=THIS_MODULE)
# def test_one_arg_positional(case_data):
#     """ Tests the decorator with one positional argument @my_decorator(goo) """
#
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     help(replace_by_foo)
#     print(args_info)
#
#     # why would this test fail ?
#     expected_failure_msg = None
#     if args_info.nb_args == 0:
#         expected_failure_msg = "there are no arguments"
#     elif args_info.nb_mandatory_args > 1:
#         expected_failure_msg = "there are too many mandatory arguments"
#     elif args_info.first_arg_name == "replacement" and not is_first_arg_protected:
#         # note: if the first arg name is not 'replacement', this test will not send a callable positional argument
#         # so it should not fail.
#         expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#
#     if expected_failure_msg is None:
#         print("This is supposed to work")
#
#         if args_info.first_arg_name == "replacement":
#             @replace_by_foo(goo)
#             def bar():
#                 pass
#
#             assert bar is goo
#         else:
#             @replace_by_foo('dummy')
#             def bar():
#                 pass
#
#             assert bar is foo
#     else:
#         print("this is supposed to fail because %s" % expected_failure_msg)
#
#         if args_info.first_arg_name == "replacement":
#             with pytest.raises(TypeError):
#                 @replace_by_foo(goo)
#                 def bar():
#                     pass
#
#         else:
#             with pytest.raises(TypeError):
#                 @replace_by_foo('dummy')
#                 def bar():
#                     pass
#
#
# @cases_data(module=THIS_MODULE)
# def test_replacement_arg_kw(case_data):
#     """ Tests the decorator in a with-empty-parenthesis way @my_decorator() """
#
#     replace_by_foo, args_info, is_first_arg_protected = case_data.get()
#     help(replace_by_foo)
#     print(args_info)
#
#     # why would this test fail ?
#     expected_failure_msg = None
#     if not args_info.has_replacement_kwarg:
#         expected_failure_msg = "'replacement' kw arg is not present in the signature"
#         expected_err_type = TypeError
#     elif args_info.nb_mandatory_args > 1:
#         expected_failure_msg = "there are too many mandatory arguments"
#         expected_err_type = TypeError
#     elif args_info.nb_mandatory_args == 1:
#         if not args_info.first_arg_name == 'replacement':
#             expected_failure_msg = "the mandatory argument is not 'replacement'"
#             expected_err_type = TypeError
#         elif not is_first_arg_protected:
#             expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#             expected_err_type = AmbiguousFirstArgumentTypeError
#     elif args_info.nb_mandatory_args == 0 and args_info.first_arg_name == "replacement" and not is_first_arg_protected:
#         # note: if the first argument is not 'replacement', then it will receive its own default value that will
#         # probably be acceptable (i.e. not a callable nor a class)
#         expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#         expected_err_type = AmbiguousFirstArgumentTypeError
#
#     if expected_failure_msg is None:
#         print("This is supposed to work")
#
#         @replace_by_foo(replacement=goo)
#         def bar():
#             pass
#
#         assert bar is goo
#     else:
#         print("this is supposed to raise a '%s' because %s" % (expected_err_type, expected_failure_msg))
#
#         with pytest.raises(expected_err_type):
#             @replace_by_foo(replacement=goo)
#             def bar():
#                 pass
#
#
# @cases_data(module=THIS_MODULE)
# def test_dummy_arg_kw(case_data):
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
#     elif args_info.nb_mandatory_args > 1:
#         expected_failure_msg = "there are too many mandatory arguments"
#         expected_err_type = TypeError
#     elif args_info.nb_mandatory_args == 1 and not args_info.first_arg_name == 'dummy':
#         expected_failure_msg = "the mandatory argument is not 'dummy'"
#         expected_err_type = TypeError
#
#     # this test does not try to pass another type of argument for the first one so that's ok
#     # elif args_info.first_arg_name == "replacement" and not is_first_arg_protected:
#     #     expected_failure_msg = "this is an ambiguous case and the first argument is not protected"
#     #     expected_err_type = AmbiguousFirstArgumentTypeError
#
#     if expected_failure_msg is None:
#         print("This is supposed to work")
#
#         @replace_by_foo(dummy='hello')
#         def bar():
#             pass
#
#         assert bar is foo
#     else:
#
#         print("this is supposed to raise a '%s' because %s" % (expected_err_type, expected_failure_msg))
#
#         with pytest.raises(expected_err_type):
#             @replace_by_foo(dummy='hello')
#             def bar():
#                 pass
#
#
# # TODO two args positional
# # TODO one arg positional one arg kw
#
#
# @cases_data(module=THIS_MODULE)
# @pytest.mark.parametrize('new_val_for_dummy', ['hello', DEFAULT_DUMMY_VALUE])
# def test_two_args_kw_both_orders(case_data, new_val_for_dummy):
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
#
#
# def test_var_positional():
#     # put your breakpoints here :)
#     print()
#
#     def foo():
#         pass
#
#     @decorator()
#     def replace_by_foo(*args, f=DECORATED):
#         return foo
#
#     with pytest.raises(AmbiguousFirstArgumentTypeError):
#         @replace_by_foo
#         def bar():
#             pass
#
#     @replace_by_foo()
#     def bar():
#         pass
#
#     assert bar is foo
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
#     return Details(nb_mandatory_args=nb_mandatory_args, nb_optional_args=nb_optional_args,
#                    first_arg_name=first_arg_name, has_dummy_kwarg=has_dummy_kwarg,
#                    has_replacement_kwarg=has_replacement_kwarg)
