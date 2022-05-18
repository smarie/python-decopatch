"""
Tests in this file do almost nothing at runtime, but serve as a source for
testing with pyright from test_typing.py
"""
from typing import Any, Callable

import pytest

from decopatch import DECORATED, function_decorator


def test_invalid_parameter():
    with pytest.raises(TypeError):
        # Error, invalid argument.
        # This triggers error in type checking and in runtime.
        @function_decorator(invalid_param=True)
        def decorator_with_invalid_param(fn=DECORATED):
            return fn


def test_normal_decorator():
    @function_decorator
    def decorator(scope="test", fn=DECORATED):  # type: (str, Any) -> Callable[..., Any]
        return fn

    # Ok
    @decorator
    def decorated_flat():
        pass

    # Ok, should reveal correct type for `scope`
    @decorator(scope="success")
    def decorated_with_valid_options():
        pass

    # Error, Literal[2] is incompatible with str
    @decorator(scope=2)
    def decorated_with_invalid_options():
        pass


def test_function_decorator_with_params():
    # Ok, should reveal correct type for `enable_stack_introspection`
    @function_decorator(enable_stack_introspection=True)
    def decorator_with_params(scope = "test", fn=DECORATED):  # type: (str, Any) -> Callable[..., Any]
        return fn

    # Ok, should reveal correct type for `scope`
    @decorator_with_params(scope="success")
    def decorated_with_valid_options():
        pass

    @decorator_with_params(scope=2)
    def decorated_with_invalid_options():
        pass
