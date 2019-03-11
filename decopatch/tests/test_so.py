from __future__ import print_function

import logging

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


@pytest.mark.parametrize('mode', ['flat', 'double-flat'], ids="mode={}".format)
def test_so_2(mode):
    """
    Tests that the solution posted at
    https://stackoverflow.com/questions/52126071/decorator-with-arguments-avoid-parenthesis-when-no-arguments/55106984#55106984
    Actually works
    """
    if mode == 'flat':
        @function_decorator
        def logged(disabled=False, logger=logging.getLogger('default'), func=DECORATED):

            # (1) create a signature-preserving wrapper
            @wraps(func)
            def _func_wrapper(*f_args, **f_kwargs):
                # stuff
                result = func(*f_args, **f_kwargs)
                # stuff
                return result

            # (2) return it
            return _func_wrapper
    else:
        @function_decorator
        def logged(disabled=False, logger=logging.getLogger('default'),
                   func=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
            # this is directly the signature-preserving wrapper
            # stuff
            result = func(*f_args, **f_kwargs)
            # stuff
            return result

    @logged(disabled=True)
    def foo():
        pass

    @logged
    def bar():
        pass

    foo()

    bar()


@pytest.mark.parametrize('mode', ['flat', 'double-flat'], ids="mode={}".format)
def test_so_3(mode):
    """
    Checks that the answer at
    https://stackoverflow.com/a/55107188/7262247
    works correctly
    :param mode:
    :return:
    """

    if mode == 'flat':
        @function_decorator
        def foo_register(method_name=None, method=DECORATED):
            if method_name is None:
                method.gw_method = method.__name__
            else:
                method.gw_method = method_name

            # create a signature-preserving wrapper
            @wraps(method)
            def wrapper(*args, **kwargs):
                method(*args, **kwargs)

            return wrapper
    else:
        @function_decorator
        def foo_register(method_name=None,
                         method=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
            # this is directly the wrapper
            if method_name is None:
                method.gw_method = method.__name__
            else:
                method.gw_method = method_name

            method(*f_args, **f_kwargs)

    @foo_register
    def my_function():
        print('hi...')

    @foo_register('say_hi')
    def my_function():
        print('hi...')

