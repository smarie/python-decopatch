# This is test file for typing,
# No automatic testing is used at the moment. Just use your type checker and see if it works.
from decopatch import DECORATED, function_decorator


@function_decorator
def decorator(scope: str = "test", f=DECORATED):
    pass

# Ok, should reveal coorect type for `enable_stack_introspection`
@function_decorator(enable_stack_introspection=True)
def decorator_with_params(scope: str = "test", f=DECORATED):
    pass


# Error, invalid argument
@function_decorator(invalid_param=True)
def decorator_wint_invalid_param():
    pass

# Ok
@decorator
def decorated_flat():
    pass

# Error, Literal[2] is incompatible with str
@decorator(scope=2)
def decorated_with_invalid_options():
    pass

# Ok, should reveal coorect type for `scope`
@decorator(scope="success")
def decorated_with_valid_options():
    pass


# Ok, should reveal coorect type for `scope`
@decorator_with_params(scope="success")
def decorated_with_valid_options_v2():
    pass
