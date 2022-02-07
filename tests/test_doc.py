from __future__ import print_function


import pytest
from makefun import wraps

from decopatch import function_decorator, DECORATED, WRAPPED, F_ARGS, F_KWARGS, decorator

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


@pytest.mark.parametrize('flat_mode', [False, True], ids="flat_mode={}".format)
def test_doc_add_tag_function(flat_mode):
    """ Tests that the @add_tag example from doc (functions only) works """

    if not flat_mode:
        @function_decorator
        def add_tag(tag='hi!'):
            """
            Example decorator to add a 'tag' attribute to a function.
            :param tag: the 'tag' value to set on the decorated function (default 'hi!).
            """
            def apply_decorator(f):
                """
                This is the method that will be called when your decorator is used on a
                function `f`. It should return the replacement for this function (it can
                be the same object, or another one, not even a function!)
                """
                setattr(f, 'tag', tag)
                return f

            return apply_decorator

    else:
        @function_decorator
        def add_tag(tag='hi!', f=DECORATED):
            """
            Example decorator to add a 'tag' attribute to a function.
            :param tag: the 'tag' value to set on the decorated function (default 'hi!).
            """
            setattr(f, 'tag', tag)
            return f

    @add_tag
    def foo():
        pass

    assert foo.tag == 'hi!'

    @add_tag()
    def foo():
        pass

    assert foo.tag == 'hi!'

    @add_tag('hello')
    def foo():
        pass

    assert foo.tag == 'hello'

    # manual mode
    add_tag()(foo)
    assert foo.tag == 'hi!'

    # signature and help
    assert "%s%s" % (add_tag.__name__, signature(add_tag)) == "add_tag(tag='hi!')"
    print(help(add_tag))
    assert add_tag.__doc__ == """
            Example decorator to add a 'tag' attribute to a function.
            :param tag: the 'tag' value to set on the decorated function (default 'hi!).
            """
    assert add_tag.__module__ == test_doc_add_tag_function.__module__


@pytest.mark.parametrize('mode', ['nested', 'flat', 'double-flat'])
def test_doc_say_hello(capsys, mode):
    """ Tests that the @say_hello example from doc works """

    with capsys.disabled():
        if mode == 'nested':
            @function_decorator
            def say_hello(person="world", f=DECORATED):
                """
                This decorator wraps the decorated function so that a nice hello
                message is printed before each call.

                :param person: the person name in the print message. Default = "world"
                """

                # create a wrapper of f that will do the print before call
                # we rely on `makefun.wraps` to preserve signature
                @wraps(f)
                def new_f(*args, **kwargs):
                    print("hello, %s !" % person)  # say hello
                    return f(*args, **kwargs)  # call f

                # return the new function
                return new_f
        elif mode == 'flat':
            @function_decorator
            def say_hello(person="world", f=DECORATED):
                """
                This decorator wraps the decorated function so that a nice hello
                message is printed before each call.

                :param person: the person name in the print message. Default = "world"
                """

                # create a wrapper of f that will do the print before call
                # we rely on `makefun.wraps` to preserve signature
                @wraps(f)
                def new_f(*args, **kwargs):
                    print("hello, %s !" % person)  # say hello
                    return f(*args, **kwargs)  # call f

                # return the new function
                return new_f

        elif mode == 'double-flat':
            @function_decorator
            def say_hello(person="world", f=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
                """
                This decorator wraps the decorated function so that a nice hello
                message is printed before each call.

                :param person: the person name in the print message. Default = "world"
                """
                print("hello, %s !" % person)  # say hello
                return f(*f_args, **f_kwargs)  # call f

        else:
            raise ValueError("unsupported mode : %s" % mode)

    # for debug..
    with capsys.disabled():
        @say_hello  # no parenthesis
        def foo():
            print("<executing foo>")

    # for debug..
    with capsys.disabled():
        foo()

    foo()

    @say_hello()  # empty parenthesis
    def bar():
        print("<executing bar>")

    bar()

    @say_hello("you")  # arg
    def custom():
        print("<executing custom>")

    custom()

    # manual decoration
    def custom2():
        print("<executing custom2>")

    custom2 = say_hello()(custom2)
    custom2()

    help(say_hello)

    assert str(signature(say_hello)) == "(person='world')"

    print("Signature: %s" % signature(say_hello))

    @say_hello  # no parenthesis
    def add_ints(a, b):
        return a + b

    assert add_ints(1, 3) == 4

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """hello, world !
<executing foo>
hello, world !
<executing bar>
hello, you !
<executing custom>
hello, world !
<executing custom2>
Help on function say_hello in module tests.test_doc:

say_hello(person='world')
    This decorator wraps the decorated function so that a nice hello
    message is printed before each call.
    
    :param person: the person name in the print message. Default = "world"

Signature: (person='world')
hello, world !
"""

    assert captured.err == ""


@pytest.mark.parametrize('flat_mode', [False, True], ids="flat_mode={}".format)
def test_doc_add_tag_class_and_function(flat_mode):
    """ Tests that the @add_tag example from doc (function + class) works """

    if not flat_mode:
        @decorator
        def add_tag(tag='hi!'):
            """
            Example decorator to add a 'tag' attribute to a function or class. It can be
            used with and without parenthesis, with and without arguments.

            :param tag: the 'tag' value to set on the decorated item (default 'hi!).
            """

            def _apply_decorator(o):
                """
                This is the method that will be called when your decorator is used on an
                object `i`. It should return the replacement for this object (it can
                be the same object, or another one, not even the same type!)
                """
                setattr(o, 'tag', tag)
                return o

            return _apply_decorator

    else:
        @decorator
        def add_tag(tag='hi!', o=DECORATED):
            """
            Example decorator to add a 'tag' attribute to a function or class. It can be
            used with and without parenthesis, with and without arguments.

            :param tag: the 'tag' value to set on the decorated item (default 'hi!).
            """
            setattr(o, 'tag', tag)
            return o

    @add_tag
    def foo():
        pass

    assert foo.tag == 'hi!'

    @add_tag()
    def foo():
        pass

    assert foo.tag == 'hi!'

    @add_tag('hello')
    def foo():
        pass

    assert foo.tag == 'hello'

    # manual mode
    add_tag()(foo)
    assert foo.tag == 'hi!'

    # classes

    @add_tag
    class Foo():
        pass

    assert Foo.tag == 'hi!'

    @add_tag()
    class Foo():
        pass

    assert Foo.tag == 'hi!'

    @add_tag('hello')
    class Foo():
        pass

    assert Foo.tag == 'hello'

    # manual mode
    add_tag()(Foo)
    assert Foo.tag == 'hi!'

    print(help(add_tag))

    assert str(signature(add_tag)) == "(tag='hi!')"

