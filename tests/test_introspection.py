import pytest

from decopatch.utils_disambiguation import disambiguate_using_introspection, FirstArgDisambiguation, \
    SUPPORTS_INTROSPECTION


@pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")
def test_on_functions():

    def level1(arg):
        return disambiguate_using_introspection(3, arg)

    def my_decorator(arg):
        my_decorator.res = level1(arg)
        if my_decorator.res is FirstArgDisambiguation.is_decorated_target:
            return "replacement"
        elif my_decorator.res is FirstArgDisambiguation.is_normal_arg:
            def _apply(f):
                return "replacement"
            return _apply
        else:
            raise Exception()

    # trying to use the trick to see if that perturbates the introspection
    # my_decorator.__wrapped__ = level1

    @my_decorator
    def foo():
        pass

    assert my_decorator.res == FirstArgDisambiguation.is_decorated_target

    @my_decorator(foo)
    def foo():
        pass

    assert my_decorator.res == FirstArgDisambiguation.is_normal_arg
