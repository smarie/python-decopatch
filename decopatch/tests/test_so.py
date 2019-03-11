from __future__ import print_function

import pytest

from decopatch import function_decorator, WRAPPED, F_ARGS, F_KWARGS, DECORATED
from makefun import wraps


def test_so_flat():
    """
    Tests that answer at
    https://stackoverflow.com/questions/28693930/when-to-use-decorator-and-decorator-factory/55078327#55078327 is
    working
    """
    @function_decorator
    def before_run(func=DECORATED):
        @wraps(func)
        def _execute(*f_args, **f_kwargs):
            print("hello from before run")
            if f_kwargs['a'] > 0:
                f_kwargs['a'] = 100
            return func(*f_args, **f_kwargs)
        return _execute

    @before_run
    def running_func(a, b):
        print("a", a, "b", b)
        return a + b

    assert running_func(-1, 2) == 1
    assert running_func(1, 2) == 102


def test_so_double_flat():
    """
    Tests that answer at
    https://stackoverflow.com/questions/28693930/when-to-use-decorator-and-decorator-factory/55078327#55078327 is
    working
    """
    @function_decorator
    def before_run(func=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
        print("hello from before run")
        if f_kwargs['a'] > 0:
            f_kwargs['a'] = 100
        return func(*f_args, **f_kwargs)

    @before_run
    def running_func(a, b):
        print("a", a, "b", b)
        return a + b

    assert running_func(-1, 2) == 1
    assert running_func(1, 2) == 102


@pytest.mark.parametrize('style', ['flat', 'double-flat'], ids="style={}".format)
def test_so_wrap(style):
    """
    Tests that the answer at
    https://stackoverflow.com/a/55105198/7262247
    works correctly
    :return:
    """
    if style == 'flat':
        @function_decorator
        def makestyle(style='b', fn=DECORATED):
            open_tag = "<%s>" % style
            close_tag = "</%s>" % style

            @wraps(fn)
            def wrapped(*args, **kwargs):
                return open_tag + fn(*args, **kwargs) + close_tag

            return wrapped
    else:
        @function_decorator
        def makestyle(style='b', fn=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
            open_tag = "<%s>" % style
            close_tag = "</%s>" % style
            return open_tag + fn(*f_args, **f_kwargs) + close_tag

    @makestyle
    @makestyle('i')
    def hello(who):
        return "hello %s" % who

    assert hello('world') == '<b><i>hello world</i></b>'

    # you can check that
    with pytest.raises(TypeError):
        hello()  # TypeError: hello() missing 1 required positional argument: 'who'
