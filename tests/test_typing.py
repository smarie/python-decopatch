# This is test file for typing,
# No automatic testing is used at the moment. Just use your type checker and see if it works.
# Pytest here is used to make sure that runtime behavir matches with type checker expecter errors.
from decopatch import DECORATED, function_decorator
import pytest


def test_invalid_parameter():
    with pytest.raises(TypeError):
        # Error, invalid argument
        @function_decorator(invalid_param=True)
        def decorator_wint_invalid_param(fn=DECORATED):
            return fn


def test_normal_decorator():
    @function_decorator
    def decorator(scope: str = "test", fn=DECORATED):
        assert isinstance(scope, str)
        return fn

    # Ok
    @decorator
    def decorated_flat():
        pass

    assert decorated_flat

    with pytest.raises(AssertionError):
        # Error, Literal[2] is incompatible with str
        @decorator(scope=2)
        def decorated_with_invalid_options():
            pass

    # Ok, should reveal correct type for `scope`
    @decorator(scope="success")
    def decorated_with_valid_options():
        pass

    assert decorated_with_valid_options


def test_function_decorator_with_params():
    # Ok, should reveal correct type for `enable_stack_introspection`
    @function_decorator(enable_stack_introspection=True)
    def decorator_with_params(scope: str = "test", fn=DECORATED):
        return fn

    # Ok, should reveal correct type for `scope`
    @decorator_with_params(scope="success")
    def decorated_with_valid_options():
        pass

    assert decorated_with_valid_options
