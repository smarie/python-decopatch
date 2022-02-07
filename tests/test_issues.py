import sys

import pytest

from decopatch import class_decorator, DECORATED, function_decorator


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


def test_disambiguation_during_binding():
    @function_decorator
    def my_decorator(a, *args, **kwargs):
        def apply(f):
            return f
        return apply

    @my_decorator("hello", 12)
    class Foo:
        pass


def test_varpositional():
    if sys.version_info < (3, 0):
        pytest.skip("test skipped in python 2.x because syntax is not compliant")
    else:
        from ._test_issues_py3 import create_test_varpositional
        replace_with = create_test_varpositional()

        @replace_with(1, 2, 3)
        class Foo(object):
            pass

        # check that Foo has been replaced with (1, 2, 3)
        assert len(Foo) == 3
