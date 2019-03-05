from __future__ import print_function
import sys
from copy import copy
from enum import Enum

import pytest

from pytest_cases import cases_data, THIS_MODULE, cases_generator, case_name
from decopatch import decorator, DECORATED, AmbiguousFirstArgumentTypeError, InvalidMandatoryArgError, \
    AmbiguousDecoratorDefinitionError
from decopatch.tests.test_main2_parametrizers import case_no_parenthesis, case_empty_parenthesis, foo, \
    case_one_arg_positional_callable, case_one_arg_positional_noncallable, case_one_arg_positional_noncallable_default, \
    case_one_kwarg_callable, case_one_kwarg_noncallable, \
    case_one_kwarg_noncallable_default, is_foo_or_goo, case_two_args_positional_callable_first, \
    case_two_args_positional_callable_last, case_two_args_positional_callable_first_dummy_default, \
    case_two_args_positional_callable_last_dummy_default, goo, DEFAULT_DUMMY_VALUE
from decopatch.tests import test_main2_parametrizers

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


# -------------
class codes(Enum):
    success = 0
    skip = 1

SUCCESS = codes.success
SKIP = codes.skip


@case_name("easy_0_args(f=DECORATED)")
def case_easy_0_args(parametrizer):
    """
    This decorator has no arguments and can therefore be used with and without parenthesis
    """

    # Note: we will decorate it later, otherwise the get_args_info will not be accurate in this particular case
    # @decorator
    def replace_by_foo(f=DECORATED):
        return foo

    # get_args_info(replace_by_foo),
    expected_err = {case_no_parenthesis: SUCCESS,
                    case_empty_parenthesis: SUCCESS}

    default_value = (TypeError, "python does not allow f(x) if f has 0 args")

    return decorator(replace_by_foo), expected_err.get(parametrizer.f, default_value)


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3 or higher")
@case_name("easy_0_args(*, f=DECORATED)")
def case_easy_0_args_kwonly(parametrizer):
    """
    This decorator has no arguments and can therefore be used with and without parenthesis
    """
    # only do it if we are in the appropriate python version
    evaldict = copy(globals())
    evaldict.update(locals())
    exec("""
def replace_by_foo(*, f=DECORATED):
    return foo
""", evaldict)
    replace_by_foo = evaldict['replace_by_foo']

    # get_args_info(replace_by_foo),
    expected_err = {case_no_parenthesis: SUCCESS,
                    case_empty_parenthesis: SUCCESS}

    default_value = (TypeError, "python does not allow f(x) if f has 0 args")

    return decorator(replace_by_foo), expected_err.get(parametrizer.f, default_value)


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3 or higher")
def case_hard_varpositional(parametrizer):

    # only do it if we are in the appropriate python version
    evaldict = copy(globals())
    evaldict.update(locals())
    exec("""
@decorator(can_first_arg_be_ambiguous=True, enable_stack_introspection=False)
def replace_by_foo(*args, f=DECORATED):
    # tolerant to any order of arguments: 'goo' will be returned if found
    for a in args:
        if a is goo:
            return a
    return foo
""", evaldict)
    replace_by_foo = evaldict['replace_by_foo']

    # common expected errors
    expected_err = {
        # not protected: by default
        case_no_parenthesis: (AmbiguousFirstArgumentTypeError, "using the decorator without parenthesis mimics "
                                                               "usage with a single arg."),
        case_one_arg_positional_callable: (AmbiguousFirstArgumentTypeError, "calling a non-protected decorator "
                                                                            "with a callable leads to an error"),
        case_one_kwarg_callable: (SKIP, "decorator impl does not accept keyword args"),
        case_one_kwarg_noncallable: (SKIP, "decorator impl does not accept keyword args"),
        case_one_kwarg_noncallable_default: (SKIP, "decorator impl does not accept keyword args"),
    }

    # if parametrizer.f in {case_no_parenthesis, case_one_arg_positional_callable}:
    #     print()

    default_value = SUCCESS

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@cases_generator("{protection}_1m_arg(dummy, f=DECORATED)", protection=['unprotected(explicit)', 'protected(default)'])
def case_hard_1_m_0_opt_noncallable(parametrizer, protection):
    """
    This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis
    """
    protected = (protection == 'protected(default)')

    if not protected:
        # we unprotect it explicitly
        @decorator(can_first_arg_be_ambiguous=True, enable_stack_introspection=False)
        def replace_by_foo(dummy, f=DECORATED):
            return foo
    else:
        # default: we protect it by saying that first arg can not be a function/class
        @decorator(enable_stack_introspection=False)
        def replace_by_foo(dummy, f=DECORATED):
            return foo

    # common expected errors
    expected_err = {
        # case_no_parenthesis
        case_empty_parenthesis: (TypeError, "python does not allow f() if f has 1 mandatory arg"),
        # case_one_arg_positional_callable
        case_one_arg_positional_noncallable: SUCCESS,
        case_one_arg_positional_noncallable_default: SUCCESS,
        case_one_kwarg_callable: (SKIP, "decorator impl does not have a 'replacement' arg"),
        case_one_kwarg_noncallable: SUCCESS,
        case_one_kwarg_noncallable_default: SUCCESS,
    }

    # errors that protection changes
    if not protected:
        expected_err.update({
            case_no_parenthesis: (AmbiguousFirstArgumentTypeError, "using the decorator without parenthesis mimics "
                                                                   "usage with a single arg."),
            case_one_arg_positional_callable: (AmbiguousFirstArgumentTypeError, "calling a non-protected decorator "
                                                                                "with a callable leads to an error"),
        })
    else:
        expected_err.update({
            case_no_parenthesis: (InvalidMandatoryArgError, "a no-parenthesis usage will be declared by the "
                                                            "disambiguator as decorated target"),
            case_one_arg_positional_callable: (InvalidMandatoryArgError, "calling with a single positional callable"
                                                                         "will be declared by "
                                                                         "the disambiguator as decorated target"),
        })

    # if protected and parametrizer.f is case_no_parenthesis:
    #     print()

    default_value = (TypeError, "python does not allow 2 args if f has 1 arg")

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@cases_generator("{protection}_1m_arg(replacement, f=DECORATED)_kwonly={kw_only}", protection=['protected(default)',
                                                                              'protected(explicit)'],
                 kw_only=[False, True])
def case_hard_1_m_0_opt_callable(parametrizer, protection, kw_only):
    """This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis"""

    protected_explicit = (protection == 'protected(explicit)')

    if not protected_explicit:
        @decorator(enable_stack_introspection=False)  # (can_first_arg_be_ambiguous=True)
        def replace_by_foo(replacement, f=DECORATED):
            return replacement
    else:
        # we protect it by saying that
        # - first argument should be one of {foo, goo},
        # - and that otherwise it is sure that it is a no-parenthesis call
        @decorator(callable_or_cls_firstarg_disambiguator=is_foo_or_goo, enable_stack_introspection=False)
        def replace_by_foo(replacement, f=DECORATED):
            return replacement

    # common expected errors
    expected_err = {
        # case_no_parenthesis
        case_empty_parenthesis: (TypeError, "python does not allow f() if f has 1 mandatory arg"),
        # case_one_arg_positional_callable
        case_one_arg_positional_noncallable: (SKIP, "This decorator does not access a noncallable positional arg"),
        case_one_arg_positional_noncallable_default: (SKIP, "This decorator does not access a noncallable positional "
                                                            "arg"),
        # case_one_kwarg_callable
        case_one_kwarg_noncallable: (SKIP, "decorator impl does not have a 'dummy' arg"),
        case_one_kwarg_noncallable_default: (SKIP, "decorator impl does not have a 'dummy' arg"),
    }

    # errors that protection changes
    if not protected_explicit:
        # note : when can_first_arg_be_ambiguous=True the errors would be 'AmbiguousFirstArgumentTypeError'
        expected_err.update({
            case_no_parenthesis: (InvalidMandatoryArgError, "using the decorator without parenthesis mimics "
                                                                   "usage with a single arg."),
            case_one_arg_positional_callable: (InvalidMandatoryArgError, "calling a decorator with a callable as first "
                                                                         "and only non-default argument leads by "
                                                                         "default to an error"),
            case_one_kwarg_callable: (InvalidMandatoryArgError, "calling a decorator with a callable as first "
                                                                         "and only non-default argument leads by "
                                                                         "default to an error"),
        })
    else:
        expected_err.update({
            case_no_parenthesis: (InvalidMandatoryArgError, "a no-parenthesis usage will be declared by the "
                                                            "disambiguator as decorated target"),
            case_one_arg_positional_callable: SUCCESS,
            case_one_kwarg_callable: SUCCESS,
        })

    default_value = (TypeError, "python does not allow 2 args if f has 1 arg")

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@case_name("easy_2m_args(replacement, dummy, f=DECORATED)")
def case_easy_2_m_0_opt_callable_first(parametrizer):
    @decorator
    def replace_by_foo(replacement, dummy, f=DECORATED):
        return replacement

    # get_args_info(replace_by_foo),
    expected_err = {
        case_two_args_positional_callable_first: SUCCESS,
        case_two_args_positional_callable_last: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_first_dummy_default: SUCCESS,
        case_two_args_positional_callable_last_dummy_default: (SKIP, "the order of positional args in the test does not match"),
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@case_name("easy_2m_args(dummy, replacement, f=DECORATED)")
def case_easy_2_m_0_opt_callable_last(parametrizer):
    @decorator
    def replace_by_foo(dummy, replacement, f=DECORATED):
        return replacement

    # get_args_info(replace_by_foo),
    expected_err = {
        case_two_args_positional_callable_first: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last: SUCCESS,
        case_two_args_positional_callable_first_dummy_default: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last_dummy_default: SUCCESS
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@case_name("easy_2m_args(dummy, dummy2, f=DECORATED)")
def case_easy_2_m_0_opt_no_callable(parametrizer):
    @decorator
    def replace_by_foo(dummy, dummy2, f=DECORATED):
        return goo

    # get_args_info(replace_by_foo),
    expected_err = {
        case_two_args_positional_callable_first: SUCCESS,
        case_two_args_positional_callable_last: SUCCESS,
        case_two_args_positional_callable_first_dummy_default: SUCCESS,
        case_two_args_positional_callable_last_dummy_default: SUCCESS,
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@cases_generator("{protection}_2opt(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED)",
                 protection=['unprotected(explicit)', 'protected(explicit)'])
def case_hard_0_m_2_opt_callable_last(parametrizer, protection):

    protected = (protection == 'protected(explicit)')

    if not protected:
        # check that by default there is an error so the unprotected case can not happen anymore
        with pytest.raises(AmbiguousDecoratorDefinitionError):
            @decorator(enable_stack_introspection=False, can_first_arg_be_ambiguous=None)
            def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED):
                return replacement if replacement is not None else foo

        @decorator(can_first_arg_be_ambiguous=True, enable_stack_introspection=False)
        def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED):
            return replacement if replacement is not None else foo
    else:
        # we protect it by saying that first arg can not be a function/class
        @decorator(can_first_arg_be_ambiguous=False)
        def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None, f=DECORATED):
            return replacement if replacement is not None else foo

    # common expected errors
    expected_err = {
        case_one_arg_positional_callable: (SKIP, "the first positional arg is supposed not to be the callable here"),
        case_two_args_positional_callable_first: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_first_dummy_default: (SKIP, "the order of positional args in the test does "
                                                                      "not match"),
    }

    # errors that protection changes
    if not protected:
        expected_err.update({
            case_no_parenthesis: (AmbiguousFirstArgumentTypeError, "using the decorator without parenthesis mimics "
                                                                   "usage with a single arg."),
        })

    # if protected and parametrizer.f is case_no_parenthesis:
    #     print()

    default_value = SUCCESS

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


@cases_generator("{protection}_2opt(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED)",
                 protection=['unprotected(explicit)', 'protected(explicit)'])
def case_hard_0_m_2_opt_callable_first(parametrizer, protection):

    protected = (protection == 'protected(explicit)')

    if not protected:
        # check that by default there is an error so the unprotected case can not happen anymore
        with pytest.raises(AmbiguousDecoratorDefinitionError):
            @decorator(enable_stack_introspection=False, can_first_arg_be_ambiguous=None)
            def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED):
                return replacement if replacement is not None else foo

        # unprotected explicitly
        @decorator(can_first_arg_be_ambiguous=True, enable_stack_introspection=False)
        def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED):
            return replacement if replacement is not None else foo
    else:
        # we protect it by saying that first arg should be either foo or goo
        @decorator(callable_or_cls_firstarg_disambiguator=is_foo_or_goo)
        def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE, f=DECORATED):
            return replacement if replacement is not None else foo

    # common expected errors
    expected_err = {
        case_one_arg_positional_noncallable: (SKIP, "the first positional arg is supposed to be the callable here"),
        case_one_arg_positional_noncallable_default: (SKIP, "the first positional arg is supposed to be the callable here"),
        case_two_args_positional_callable_last: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last_dummy_default: (SKIP, "the order of positional args in the test does not match"),
    }

    # errors that protection changes
    if not protected:
        expected_err.update({
            # this is with the ambiguous protection "on"
            case_no_parenthesis: (AmbiguousFirstArgumentTypeError, "using the decorator without parenthesis mimics "
                                                                   "usage with a single arg."),
            case_one_arg_positional_callable: (AmbiguousFirstArgumentTypeError, "calling a non-protected decorator "
                                                                                "with a callable leads to an error"),
            case_one_kwarg_callable: (AmbiguousFirstArgumentTypeError, "calling a non-protected decorator "
                                                                       "with a callable as first and only non-default "
                                                                       "argument leads to an error"),
            case_two_args_positional_callable_first_dummy_default: (AmbiguousFirstArgumentTypeError, "calling a "
                                                                    "non-protected decorator with a callable as first "
                                                                    "and only non-default argument leads to an error"),
        })

    # if parametrizer.f is case_no_parenthesis:
    #     print()

    default_value = SUCCESS

    return replace_by_foo, expected_err.get(parametrizer.f, default_value)


# -------------------------


@cases_data(module=test_main2_parametrizers, case_data_argname='parametrizer')
@cases_data(module=THIS_MODULE)
def test_all(case_data, parametrizer):

    replace_by_foo, expected_err = case_data.get(parametrizer)

    print("Generated decorator : %s%s" % (replace_by_foo.__name__, signature(replace_by_foo)))

    print("Calling it as %s" % parametrizer.f.__name__)

    if expected_err is SUCCESS:
        print("Expected SUCCESS\n")

        created_decorator, expected_replacement = parametrizer.get(replace_by_foo, parametrizer.f.__name__)

        @created_decorator
        def bar():
            pass

        assert bar is expected_replacement
    else:
        expected_err_type, expected_failure_msg = expected_err

        if expected_err_type is SKIP:
            pytest.skip(expected_failure_msg)

        print("Expected error: '%s' because %s\n" % (expected_err_type.__name__, expected_failure_msg))

        with pytest.raises(expected_err_type):
            created_decorator, expected_replacement = parametrizer.get(replace_by_foo, parametrizer.f.__name__)

            @created_decorator
            def bar():
                pass



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
#     nb_m_args = len([p for p in params_to_check if p.default is p.empty])
#
#     # nb optional args
#     nb_opt_args = nb_args - nb_m_args
#
#     first_arg_name = params_to_check[0].name if len(params_to_check) > 0 else None
#
#     has_dummy_kwarg = len([p for p in params_to_check if p.name == 'dummy']) > 0
#     has_replacement_kwarg = len([p for p in params_to_check if p.name == 'replacement']) > 0
#
#     return ArgsDetails(nb_m_args=nb_m_args, nb_opt_args=nb_opt_args,
#                        first_arg_name=first_arg_name, has_dummy_kwarg=has_dummy_kwarg,
#                        has_replacement_kwarg=has_replacement_kwarg)
