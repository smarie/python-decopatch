import pytest

from makefun import with_signature
from decopatch import function_decorator, class_decorator, decorator, DECORATED

from inspect import isclass

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


def test_doc_impl_first_tag():
    """ The first implementation-first example in the doc """
    from decopatch import decorator, DECORATED

    @decorator
    def add_tag(tag, f=DECORATED):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :param f: represents the decorated item. Automatically injected.
        :return:
        """
        setattr(f, 'my_tag', tag)
        return f

    @add_tag('hello')
    def foo():
        return

    assert foo.my_tag == 'hello'

    with pytest.raises(TypeError):
        # add_tag() missing 1 required positional argument: 'tag'
        @add_tag
        def foo():
            return


def test_doc_impl_first_say_hello(capsys):
    """The second implementation-first example in the doc"""

    @decorator
    def say_hello(person='world', f=DECORATED):
        """
        This decorator modifies the decorated function so that a nice hello
        message is printed before the call.

        :param person: the person name in the print message. Default = "world"
        :return:
        """
        # create a wrapper of f that will do the print before call
        # we rely on `@makefun.with_signature` to preserve signature
        def new_f(*args, **kwargs):
            # nonlocal person
            person = new_f.person
            print("hello, %s !" % person)  # say hello
            return f(*args, **kwargs)  # call f

        # we use the trick at https://stackoverflow.com/a/16032631/7262247
        # to access the nonlocal 'person' variable in python 2 and 3
        # for python 3 only you can use 'nonlocal' https://www.python.org/dev/peps/pep-3104/
        new_f.person = person

        # return the wrapper
        return new_f

    @say_hello
    def foo(a, b):
        return a + b

    @say_hello()
    def bar(a, b):
        return a + b

    @say_hello("you")
    def custom(a, b):
        return a + b

    assert foo(1, 3) == 4
    assert bar(1, 3) == 4
    assert custom(1, 3) == 4

    help(say_hello)

    print("Signature: %s" % signature(say_hello))

    captured = capsys.readouterr()
    assert captured.out == "hello, world !\n" \
                           "hello, world !\n" \
                           "hello, you !\n" \
                           "Help on function say_hello in module decopatch.tests.test_doc:\n" \
                           "\n" \
                           "say_hello(person='world')\n" \
                           "    This decorator modifies the decorated function so that a nice hello\n" \
                           "    message is printed before the call.\n" \
                           "    \n" \
                           "    :param person: the person name in the print message. Default = \"world\"\n" \
                           "    :return:\n" \
                           "\n" \
                           "Signature: (person='world')\n"

    assert captured.err == ""
    with capsys.disabled():
        print(captured.out)


# def test_doc_simplistic():
#     """ In this test a simple function decorator is created using @dp.function_decorator. It simply sets a field on the target"""
#
#     @function_decorator
#     def set_a_field(a_value):
#         """Your decorator. Its signature is the one that we want users to see e.g. `@set_a_field('hello')`."""
#
#         def replace_f(f):
#             """The function that will be called at static time to replace the decorated functions"""
#
#             # In this example we simply set an attribute on the function
#             setattr(f, 'a', a_value)
#
#             # The decorated f will be replaced by this f
#             return f
#
#         return replace_f
#
#     @set_a_field('hello')
#     def foo(a):
#         pass
#
#     assert foo.a == 'hello'
#
#
# def test_doc_simple_func():
#     """ In this test a function decorator is created using @dp.function_decorator. It wraps the target functions with
#     an args storage """
#
#     store = []
#
#     @function_decorator
#     def save_on_access(var=store):
#         """The decorator. Its signature is the one that we want users to see when they type."""
#
#         def replace_f(f):
#             """The function that will be executed to replace the decorated function"""
#
#             # In this example we simply set an attribute on the function
#             setattr(f, 'is_decorated', True)
#
#             # In this other example we replace a function
#             @with_signature(f)
#             def f_wrapper(*args, **kwargs):
#                 # first save
#                 var.append((args, kwargs))
#                 # then call
#                 return f(*args, **kwargs)
#
#             return f_wrapper
#
#         return replace_f
#
#     @save_on_access
#     def foo(a):
#         pass
#
#     @save_on_access()
#     def bar(a):
#         pass
#
#     foo(1)
#     bar(2)
#
#     assert store == [((), {'a': 1}), ((), {'a': 2})]
#
#     store2 = []
#
#     @save_on_access(store2)
#     def bar2(a):
#         pass
#
#     bar2(3)
#
#     assert store == [((), {'a': 1}), ((), {'a': 2})]
#     assert store2 == [((), {'a': 3})]


# def test_doc_merged():
#
#     # todo un mode mergé, et dans decorator un argument mode='auto', 'nested', 'simple' (mergé)
#
#
#
#     @decorator()
#     def save_on_access(store, f=DECORATED):
#
#         # In this example we simply set an attribute on the function
#         setattr(f, 'is_decorated', True)
#
#         # In this other example we replace a function
#         @with_signature(f)
#         def f_wrapper(*args, **kwargs):
#             # first save
#             var.append((args, kwargs))
#             # then call
#             return f(*args, **kwargs)
#
#         return f_wrapper
#


def test_doc_advanced_failing_example1():

    # this one will fail

    @decorator
    def replace_with(g, f=DECORATED):
        """This dummy decorator will replace the decorated function with its argument"""
        return g

    _assert_fails(replace_with)


def test_doc_advanced_failing_example2():

    # this one should too

    @decorator
    def replace_with(g=None, a=None, f=DECORATED):
        """This dummy decorator will replace the decorated function with its argument"""
        return g

    _assert_fails(replace_with)


def test_doc_advanced_workaround_kw_only():

    @decorator
    def replace_with_workaround_1(*, g, f=DECORATED):
        """This dummy decorator will replace the decorated function with its argument"""
        return g

    _assert_works_correctly(replace_with_workaround_1, kw_only=True)


def test_doc_advanced_workaround_not_first_arg():

    # with type hints detection: bad idea, do not do
    # @decorator
    # def replace_with_workaround_2a(a: int = None, g=None, f=DECORATED):
    #     return g

    @decorator
    def replace_with_workaround_2b(a=None, g=None, f=DECORATED):
        if not isinstance(a, int):
            raise TypeError()
        return g

    _assert_works_correctly(replace_with_workaround_2b, kw_only=True)


def test_doc_advanced_workaround_explicit_disambiguator():
    def foo():
        pass

    @decorator(first_arg_disambiguator=lambda g: g in {foo})
    def replace_with(g, f=DECORATED):
        """This dummy decorator will replace the decorated function with its argument"""
        return g

    _assert_works_correctly(replace_with, foo=foo)


def test_doc_advanced_workaround_disable_detection():
    @decorator(disable_no_arg_detection=True)
    def replace_with(g, f=DECORATED):
        return g


def _assert_fails(replace_with):
    def foo():
        pass

    with pytest.raises(TypeError):
        @replace_with(foo)
        def bar():
            pass

    with pytest.raises(TypeError):
        @replace_with
        def bar_no_arg():
            pass


def _assert_works_correctly(replace_with, foo=None, kw_only=False):
    if foo is None:
        def foo():
            pass

    if not kw_only:
        @replace_with(foo)
        def bar():
            pass

        assert bar is foo
    else:
        with pytest.raises(TypeError):
            @replace_with(foo)
            def bar():
                pass

    @replace_with(g=foo)
    def bar():
        pass

    assert bar is foo

    with pytest.raises(TypeError):
        @replace_with
        def bar_no_arg():
            pass

