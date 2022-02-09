from __future__ import print_function

import logging
import pytest

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


from decopatch import function_decorator, WRAPPED, F_ARGS, F_KWARGS, DECORATED
from makefun import wraps, add_signature_parameters, remove_signature_parameters


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


@pytest.mark.parametrize('mode', [None, 'flat'], ids="mode={}".format)
def test_so_4(capsys, mode):
    """
    Checks that the answer at
    https://stackoverflow.com/a/55160435/7262247
    works
    """
    if mode is None:
        def my_decorator(decorator_arg1=None, decorator_arg2=False):
            # Inside the wrapper maker

            def _decorator(func):
                # (1) capture the signature of the function to wrap ...
                func_sig = signature(func)
                # ... and modify it to add new optional parameters 'new_arg1' and 'new_arg2'.
                # (if they are optional that's where you provide their defaults)
                new_arg1 = Parameter('new_arg1', kind=Parameter.POSITIONAL_OR_KEYWORD, default=False)
                new_arg2 = Parameter('new_arg2', kind=Parameter.POSITIONAL_OR_KEYWORD, default=None)
                new_sig = add_signature_parameters(func_sig, last=[new_arg1, new_arg2])

                # (2) create a wrapper with the new signature
                @wraps(func, new_sig=new_sig)
                def func_wrapper(*args, **kwds):
                    # Inside the wrapping function

                    # Pop the extra args (they will always be there, no need to provide default)
                    new_arg1 = kwds.pop('new_arg1')
                    new_arg2 = kwds.pop('new_arg2')

                    # Calling the wrapped function
                    if new_arg1:
                        print("new_arg1 True branch; new_arg2 is {}".format(new_arg2))
                        return func(*args, **kwds)
                    else:
                        print("new_arg1 False branch; new_arg2 is {}".format(new_arg2))
                        # do something with new_arg2
                        return func(*args, **kwds)

                def added_function():
                    # Do Something 2
                    print('added_function')

                func_wrapper.added_function = added_function
                return func_wrapper

            return _decorator
    else:
        @function_decorator
        def my_decorator(decorator_arg1=None, decorator_arg2=False, func=DECORATED):

            # (1) capture the signature of the function to wrap ...
            func_sig = signature(func)
            # ... and modify it to add new optional parameters 'new_arg1' and 'new_arg2'.
            # (if they are optional that's where you provide their defaults)
            new_arg1 = Parameter('new_arg1', kind=Parameter.POSITIONAL_OR_KEYWORD, default=False)
            new_arg2 = Parameter('new_arg2', kind=Parameter.POSITIONAL_OR_KEYWORD, default=None)
            new_sig = add_signature_parameters(func_sig, last=[new_arg1, new_arg2])

            # (2) create a wrapper with the new signature
            @wraps(func, new_sig=new_sig)
            def func_wrapper(*args, **kwds):
                # Inside the wrapping function

                # Pop the extra args (they will always be there, no need to provide default)
                new_arg1 = kwds.pop('new_arg1')
                new_arg2 = kwds.pop('new_arg2')

                # Calling the wrapped function
                if new_arg1:
                    print("new_arg1 True branch; new_arg2 is {}".format(new_arg2))
                    return func(*args, **kwds)
                else:
                    print("new_arg1 False branch; new_arg2 is {}".format(new_arg2))
                    # do something with new_arg2
                    return func(*args, **kwds)

            def added_function():
                # Do Something 2
                print('added_function')

            func_wrapper.added_function = added_function
            return func_wrapper

    @my_decorator(decorator_arg1=4, decorator_arg2=True)
    def foo(a, b):
        """This is my foo function"""
        print("a={}, b={}".format(a,b))

    foo(1, 2, True, 7)  # works, except if you use kind=Parameter.KEYWORD_ONLY above (in which case wont work in python 2)
    foo(1, 2, new_arg1=True, new_arg2=7)
    foo(a=3, b=4, new_arg1=False, new_arg2=42)
    foo(new_arg2=-1,b=100,a='AAA')
    foo(b=100,new_arg1=True,a='AAA')
    foo.added_function()

    help(foo)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """new_arg1 True branch; new_arg2 is 7
a=1, b=2
new_arg1 True branch; new_arg2 is 7
a=1, b=2
new_arg1 False branch; new_arg2 is 42
a=3, b=4
new_arg1 False branch; new_arg2 is -1
a=AAA, b=100
new_arg1 True branch; new_arg2 is None
a=AAA, b=100
added_function
Help on function foo in module tests.test_so:

foo(a, b, new_arg1=False, new_arg2=None)
    This is my foo function

"""


@pytest.mark.parametrize('mode', ['no-deco', None, 'flat'], ids="mode={}".format)
def test_so_5(capsys, mode):
    """
    Tests that the solution at
    https://stackoverflow.com/a/55161579/7262247
    works
    """

    if mode == 'no-deco':
        def make_test(a, b):
            """A factory to create the test function in various flavours according to meta-parameters (a, b)"""
            def test(x, y):
                print(a, b)
                print(x, y)

            # here you could play around with the created functions' identity if needed
            # test.__name__ = ...
            # test.__qualname__ = ...
            # test.__module__ = ...
            # test.__dict__ = ...
            return test

        test = make_test(a='hello', b='world')
    else:
        if mode is None:
            def more_vars(**extras):
                def wrapper(f):
                    # (1) capture the signature of the function to wrap and remove the invisible
                    func_sig = signature(f)
                    new_sig = remove_signature_parameters(func_sig, 'invisible_args')

                    # (2) create a wrapper with the new signature
                    @wraps(f, new_sig=new_sig)
                    def wrapped(*args, **kwargs):
                        # inject the invisible args again
                        kwargs['invisible_args'] = extras
                        return f(*args, **kwargs)

                    return wrapped
                return wrapper
        else:
            @function_decorator
            def more_vars(f=DECORATED, **extras):
                # (1) capture the signature of the function to wrap and remove the invisible
                func_sig = signature(f)
                new_sig = remove_signature_parameters(func_sig, 'invisible_args')

                # (2) create a wrapper with the new signature
                @wraps(f, new_sig=new_sig)
                def wrapped(*args, **kwargs):
                    kwargs['invisible_args'] = extras
                    return f(*args, **kwargs)

                return wrapped

        @more_vars(a='hello', b='world')
        def test(x, y, invisible_args):
            a = invisible_args['a']
            b = invisible_args['b']
            print(a, b)
            print(x, y)

    test(1, 2)
    help(test)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """hello world
1 2
Help on function test in module tests.test_so:

test(x, y)

"""


def test_so_6(capsys):
    """
    Tests that the answer at
    https://stackoverflow.com/a/55163391/7262247
    is correct
    """
    @function_decorator
    def my_decorator(name='my_decorator', func=DECORATED):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._decorator_name_ = name
        return wrapper

    @my_decorator
    def my_func(x):
        """my function"""
        print('hello %s' % x)

    assert my_func._decorator_name_ == 'my_decorator'
    help(my_func)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """Help on function my_func in module tests.test_so:

my_func(x)
    my function

"""
