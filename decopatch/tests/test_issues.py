import pytest

from decopatch import class_decorator, DECORATED


@pytest.mark.parametrize("position", [0, 1], ids="position={}".format)
def test_notnamed_flat_mode_varpositional(position):
    """Tests that issue https://github.com/smarie/python-decopatch/issues/12 is fixed"""

    if position == 0:
        @class_decorator
        def my_decorator(cls=DECORATED, *varpos):
            assert varpos == ("hello", 12)
            return cls
    else:
        @class_decorator
        def my_decorator(arg1, cls=DECORATED, *varpos):
            assert arg1 == "hello"
            assert varpos == (12, )
            return cls

    @my_decorator("hello", 12)
    class Foo:
        pass


@pytest.mark.parametrize("position", [0, 1], ids="position={}".format)
def test_named_flat_mode_varpositional(position):
    """Tests that issue https://github.com/smarie/python-decopatch/issues/12 is fixed"""

    if position == 0:
        @class_decorator(flat_mode_decorated_name='cls')
        def my_decorator(cls, arg1, *varpos):
            assert arg1 == "hello"
            assert varpos == (12,)
            return cls
    else:
        @class_decorator(flat_mode_decorated_name='cls')
        def my_decorator(arg1, cls, *varpos):
            assert arg1 == "hello"
            assert varpos == (12, )
            return cls

    @my_decorator("hello", 12)
    class Foo:
        pass
