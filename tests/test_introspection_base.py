import sys

import pytest
from decopatch import FirstArgDisambiguation

from decopatch.utils_disambiguation import disambiguate_using_introspection, SUPPORTS_INTROSPECTION


def generate_decorator():
    def my_deco(*args):

        def apply(f):
            my_deco.success = True
            return f

        if len(args) == 1 \
                and disambiguate_using_introspection(2, args[0]) is FirstArgDisambiguation.is_decorated_target:
            assert args[0].__name__.lower() == 'foo'
            return apply(args[0])
        else:
            return apply

    my_deco.success = False
    return my_deco


NO_PARENTHESIS = 0
EMPTY_PARENTHESIS = 1
ARGS_IN_PARENTHESIS = 2


@pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")
@pytest.mark.parametrize('is_class', [False, True], ids="isclass={}".format)
@pytest.mark.parametrize('call_mode', [NO_PARENTHESIS, EMPTY_PARENTHESIS, ARGS_IN_PARENTHESIS],
                         ids="call_mode={}".format)
def test_introspection(is_class, call_mode):

    my_deco = generate_decorator()

    if call_mode is NO_PARENTHESIS:
        if is_class:
            @my_deco
            class Foo:
                pass
        else:
            @my_deco
            def foo():
                pass
    elif call_mode is EMPTY_PARENTHESIS:
        if is_class:
            @my_deco()
            class Foo:
                pass
        else:
            @my_deco()
            def foo():
                pass
    elif call_mode is ARGS_IN_PARENTHESIS:
        if is_class:
            @my_deco(generate_decorator)
            class Foo:
                pass
        else:
            @my_deco(generate_decorator)
            def foo():
                pass

    assert my_deco.success
