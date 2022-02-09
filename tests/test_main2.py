from __future__ import print_function
import sys
from copy import copy
from enum import Enum

import pytest

from pytest_cases import parametrize, parametrize_with_cases, case, fixture
from decopatch import decorator, InvalidMandatoryArgError
from decopatch.utils_disambiguation import SUPPORTS_INTROSPECTION

from .test_main2_parametrizers import case_no_parenthesis, case_empty_parenthesis, foo, \
    case_one_arg_positional_callable, case_one_arg_positional_noncallable, case_one_arg_positional_noncallable_default, \
    case_one_kwarg_callable, case_one_kwarg_noncallable, \
    case_one_kwarg_noncallable_default, is_foo_or_goo, case_two_args_positional_callable_first, \
    case_two_args_positional_callable_last, case_two_args_positional_callable_first_dummy_default, \
    case_two_args_positional_callable_last_dummy_default, goo, DEFAULT_DUMMY_VALUE


try:  # python 3.3+
    from inspect import signature
    funcsigs_used = False
except ImportError:
    from funcsigs import signature
    funcsigs_used = True


# -------------
class NotADecoratorError(Exception):
    """Error raised my our checker after the decorator has been created, if it happens to not be a decorator. """
    pass


class codes(Enum):
    success = 0
    skip = 1


SUCCESS = codes.success
SKIP = codes.skip


@fixture
@parametrize_with_cases("p", cases=".test_main2_parametrizers")
def decorator_application_scenario(p):
    return p


@fixture
def application_case_func(decorator_application_scenario, current_cases):
    """Returns the case function used behind `decorator_application_scenario`."""
    return current_cases["decorator_application_scenario"]["p"].func


@parametrize(flat_kw_only=[False, True])
def case_easy_0_args(decorator_application_scenario, flat_kw_only, application_case_func):
    """
    This decorator has no arguments and can therefore be used with and without parenthesis
    """

    if not flat_kw_only:
        # Note: we will decorate it later, otherwise the get_args_info will not be accurate in this particular case
        @decorator
        def replace_by_foo():
            def _apply(f):
                return foo
            return _apply
    else:
        if sys.version_info < (3, 0):
            pytest.skip("requires python3 or higher")
        else:
            # only do it if we are in the appropriate python version
            from decopatch import DECORATED
            evaldict = copy(globals())
            evaldict.update(locals())
            exec("""
@decorator
def replace_by_foo(*, f=DECORATED):
    return foo
""", evaldict)
            replace_by_foo = evaldict['replace_by_foo']

    # get_args_info(replace_by_foo),
    expected = {case_no_parenthesis: SUCCESS,
                case_empty_parenthesis: SUCCESS,
                case_one_arg_positional_noncallable: (TypeError, "we correctly disambiguate by default since the "
                                                                 "argument is non-callable"),
                case_one_arg_positional_noncallable_default: (TypeError, "we correctly disambiguate by default since "
                                                                         "the argument is non-callable"),
                case_one_arg_positional_callable: (NotADecoratorError, "We are not able to disambiguate but hopefully "
                                                                       "users will realize"),
                }

    default_value = (TypeError, "python does not allow our decorator to be called with more than 1 positional, ")

    # breakpoints placeholder
    # if application_case_func is case_one_arg_positional_callable:
    #     print()

    return replace_by_foo, expected.get(application_case_func, default_value)


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3 or higher")
def case_hard_varpositional(decorator_application_scenario, current_cases):

    # only do it if we are in the appropriate python version
    evaldict = copy(globals())
    evaldict.update(locals())
    exec("""
@decorator(enable_stack_introspection=False)
def replace_by_foo(*args):
    def _apply(f):
        # tolerant to any order of arguments: 'goo' will be returned if found
        for a in args:
            if a is goo:
                return a
        return foo
    return _apply
""", evaldict)
    replace_by_foo = evaldict['replace_by_foo']

    # common expected errors
    expected = {
        # not protected: by default
        case_one_arg_positional_callable: (NotADecoratorError, "We are not able to disambiguate but hopefully "
                                                               "users will realize"),
        case_one_kwarg_callable: (TypeError, "decorator impl does not accept keyword args"),
        case_one_kwarg_noncallable: (TypeError, "decorator impl does not accept keyword args"),
        case_one_kwarg_noncallable_default: (TypeError, "decorator impl does not accept keyword args"),
    }

    application_case_func = current_cases["decorator_application_scenario"]["p"].func

    # if application_case_func in {case_no_parenthesis, case_one_arg_positional_callable}:
    #     print()

    default_value = SUCCESS

    return replace_by_foo, expected.get(application_case_func, default_value)


@parametrize(protection=[
    'default',
    pytest.param('introspection', marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
])
def case_hard_1_m_0_opt_noncallable(decorator_application_scenario, protection, current_cases):
    """
    This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis
    """
    use_introspection = (protection == 'introspection')

    @decorator(enable_stack_introspection=use_introspection)
    def replace_by_foo(dummy):
        def _apply(f):
            return foo
        return _apply

    # common expected errors
    expected = {
        case_no_parenthesis: (InvalidMandatoryArgError, "a no-parenthesis usage will be declared by the "
                                                        "default disambiguator or the stack introspecter "
                                                        "as decorated target"),
        case_empty_parenthesis: (TypeError, "python does not allow f() if f has 1 mandatory arg"),
        # case_one_arg_positional_callable:
        case_one_arg_positional_noncallable: SUCCESS,
        case_one_arg_positional_noncallable_default: SUCCESS,
        case_one_kwarg_callable: (SKIP, "decorator impl does not have a 'replacement' arg"),
        case_one_kwarg_noncallable: SUCCESS,
        case_one_kwarg_noncallable_default: SUCCESS,
    }

    if not use_introspection:
        expected.update({case_one_arg_positional_callable: (InvalidMandatoryArgError, "calling with a single positional callable"
                                                                     "will be declared by the default disambiguator or "
                                                                     "the stack introspecter as decorated target, and"
                                                                     "therefore it will say that there is something "
                                                                     "missing"),})
    else:
        expected.update({case_one_arg_positional_callable: (AssertionError, "The stack introspector will work "
                                                                            "correctly. So the decorated function"
                                                                            "will be replaced by foo. Which is not"
                                                                            "`goo`"),})

    application_case_func = current_cases["decorator_application_scenario"]["p"].func

    # if use_introspection and application_case_func is case_one_arg_positional_callable:
    #     print()

    default_value = (TypeError, "python does not allow 2 args if f has 1 arg")

    return replace_by_foo, expected.get(application_case_func, default_value)


@parametrize(protection=['protected(default)', 'protected(explicit)'], kw_only=[False, True])
def case_hard_1_m_0_opt_callable(decorator_application_scenario, protection, kw_only, current_cases):
    """This decorator has 1 mandatory argument. It has therefore a possible ambiguity when called without parenthesis"""

    protected_explicit = (protection == 'protected(explicit)')

    # the decorator impl
    def replace_by_foo(replacement):
        def _apply(f):
            return replacement
        return _apply

    if not protected_explicit:
        # as usual, but manually
        replace_by_foo = decorator()(replace_by_foo)
    else:
        # we protect it by saying that
        # - first argument should be one of {foo, goo},
        # - and that otherwise it is sure that it is a no-parenthesis call
        replace_by_foo = decorator(custom_disambiguator=is_foo_or_goo)(replace_by_foo)

    # common expected errors
    expected = {
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
        expected.update({
            case_no_parenthesis: (InvalidMandatoryArgError, "using the decorator without parenthesis mimics "
                                                                   "usage with a single arg."),
            case_one_arg_positional_callable: (InvalidMandatoryArgError, "calling a decorator with a callable as first "
                                                                         "and only non-default argument leads by "
                                                                         "default to an error"),

            # with the signature trick it is ok :
            case_one_kwarg_callable: SUCCESS,
        })
        if funcsigs_used:
            # no signature trick !
            expected.update({case_one_kwarg_callable: (InvalidMandatoryArgError, "calling a decorator with a callable as first "
                                                                         "and only non-default argument leads by "
                                                                         "default to an error"),
                             })

    else:
        expected.update({
            case_no_parenthesis: (InvalidMandatoryArgError, "a no-parenthesis usage will be declared by the "
                                                            "disambiguator as decorated target"),
            case_one_arg_positional_callable: SUCCESS,
            case_one_kwarg_callable: SUCCESS,
        })

    default_value = (TypeError, "python does not allow 2 args if f has 1 arg")

    application_case_func = current_cases["decorator_application_scenario"]["p"].func

    return replace_by_foo, expected.get(application_case_func, default_value)


@case(id="easy_2m_args(replacement, dummy)")
def case_easy_2_m_0_opt_callable_first(decorator_application_scenario, current_cases):
    @decorator
    def replace_by_foo(replacement, dummy):
        def _apply(f):
            return replacement
        return _apply

    # get_args_info(replace_by_foo),
    expected = {
        case_two_args_positional_callable_first: SUCCESS,
        case_two_args_positional_callable_last: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_first_dummy_default: SUCCESS,
        case_two_args_positional_callable_last_dummy_default: (SKIP, "the order of positional args in the test does not match"),
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    application_case_func = current_cases["decorator_application_scenario"]["p"].func

    return replace_by_foo, expected.get(application_case_func, default_value)


@case(id="easy_2m_args(dummy, replacement)")
def case_easy_2_m_0_opt_callable_last(decorator_application_scenario, application_case_func):
    @decorator
    def replace_by_foo(dummy, replacement):
        def _apply(f):
            return replacement
        return _apply

    # get_args_info(replace_by_foo),
    expected = {
        case_two_args_positional_callable_first: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last: SUCCESS,
        case_two_args_positional_callable_first_dummy_default: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last_dummy_default: SUCCESS
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    return replace_by_foo, expected.get(application_case_func, default_value)


@case(id="easy_2m_args(dummy, dummy2)")
def case_easy_2_m_0_opt_no_callable(decorator_application_scenario, application_case_func):
    @decorator
    def replace_by_foo(dummy, dummy2):
        def _apply(f):
            return goo
        return _apply

    # get_args_info(replace_by_foo),
    expected = {
        case_two_args_positional_callable_first: SUCCESS,
        case_two_args_positional_callable_last: SUCCESS,
        case_two_args_positional_callable_first_dummy_default: SUCCESS,
        case_two_args_positional_callable_last_dummy_default: SUCCESS,
    }

    default_value = (TypeError, "python does not allow < 2 args if f has 2 arg")

    return replace_by_foo, expected.get(application_case_func, default_value)


@parametrize(protection=[
    'default',
    pytest.param('introspection', marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
])
def case_hard_0_m_2_opt_callable_last(decorator_application_scenario, protection, application_case_func):

    use_introspection = (protection == 'introspection')

    @decorator(enable_stack_introspection=use_introspection)
    def replace_by_foo(dummy=DEFAULT_DUMMY_VALUE, replacement=None):
        def _apply(f):
            return replacement if replacement is not None else foo
        return _apply

    # common expected errors
    expected = {
        case_one_arg_positional_callable: (SKIP, "the first positional arg is supposed not to be the callable here"),
        case_two_args_positional_callable_first: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_first_dummy_default: (SKIP, "the order of positional args in the test does "
                                                                      "not match"),
    }

    # if protected and application_case_func is case_no_parenthesis:
    #     print()

    default_value = SUCCESS

    return replace_by_foo, expected.get(application_case_func, default_value)


@parametrize(protection=[
    'unprotected (default)',
    pytest.param('introspection', marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
    'custom_disambiguator'
])
def case_hard_0_m_2_opt_callable_first(decorator_application_scenario, protection, application_case_func):

    use_introspection = (protection == 'introspection')
    use_custom = (protection == 'custom_disambiguator')
    is_default = not use_introspection and not use_custom

    # the decorator impl
    def replace_by_foo(replacement=None, dummy=DEFAULT_DUMMY_VALUE):
        def _apply(f):
            return replacement if replacement is not None else foo

        return _apply

    if not use_custom:
        # as usual but manually
        replace_by_foo = decorator(enable_stack_introspection=use_introspection)(replace_by_foo)
    else:
        # we protect it by saying that first arg should be either foo or goo
        replace_by_foo = decorator(custom_disambiguator=is_foo_or_goo)(replace_by_foo)

    # common expected errors
    expected = {
        case_one_arg_positional_noncallable: (SKIP, "the first positional arg is supposed to be the callable here"),
        case_one_arg_positional_noncallable_default: (SKIP, "the first positional arg is supposed to be the callable here"),
        case_two_args_positional_callable_last: (SKIP, "the order of positional args in the test does not match"),
        case_two_args_positional_callable_last_dummy_default: (SKIP, "the order of positional args in the test does not match"),
    }

    # errors that protection changes
    if is_default:
        expected.update({
            case_one_arg_positional_callable: (NotADecoratorError, "No explicit exception is raised but since a "
                                                                   "double-call is made, user will probably realize "
                                                                   "that something is wrong"),
        })
        if funcsigs_used:
            # no signature trick !
            expected.update({
            case_one_kwarg_callable: (NotADecoratorError, "No explicit exception is raised but since a double-call is "
                                                          "made, user will probably realize that something is wrong"),
            case_two_args_positional_callable_first_dummy_default: (NotADecoratorError, "No explicit exception is "
                                                                                        "raised but since a double-call"
                                                                                        " is made, user will probably "
                                                                                        "realize that something is "
                                                                                        "wrong"),
            })

    default_value = SUCCESS

    # this is how you can put breakpoints
    if use_introspection and application_case_func is case_one_arg_positional_callable:
        print()

    return replace_by_foo, expected.get(application_case_func, default_value)


# -------------------------


@parametrize_with_cases("replace_by_foo, expected_err", cases=".")
def test_all(replace_by_foo, expected_err, decorator_application_scenario, application_case_func):

    # get the decorator factory, and the associated expected outcome

    print("Generated decorator : %s%s" % (replace_by_foo.__name__, signature(replace_by_foo)))
    print("Calling it as %s" % application_case_func.__name__)

    if expected_err is SUCCESS:
        print("Expected SUCCESS\n")
        execute_nominal_test(replace_by_foo, decorator_application_scenario)
    else:
        # unpack the expected error and detect SKIP scenario
        expected_err_type, expected_failure_msg = expected_err
        if expected_err_type is SKIP:
            pytest.skip(expected_failure_msg)

        # execute and assert that error of correct type is raised
        print("Expected ERROR: '%s' because %s\n" % (expected_err_type.__name__, expected_failure_msg))
        with pytest.raises(expected_err_type):
            execute_nominal_test(replace_by_foo, decorator_application_scenario)


def execute_nominal_test(replace_by_foo, decorator_application_scenario):
    """
    The actual test code: we create a decorator, check it, and apply it.

    :param replace_by_foo:
    :param decorator_application_scenario:
    :return:
    """
    created_decorator = decorator_application_scenario[0](replace_by_foo)
    expected_replacement = decorator_application_scenario[1]

    if not callable(created_decorator) or created_decorator in {foo, goo, DEFAULT_DUMMY_VALUE}:
        # this is not even a decorator, that's directly an object
        # this happens when the stack mistakenly thought that the decorator was used without argument, while it
        # was used with argument.
        raise NotADecoratorError("created decorator is not a decorator: it is %s" % created_decorator)

    @created_decorator
    def bar():
        pass

    assert bar is expected_replacement
