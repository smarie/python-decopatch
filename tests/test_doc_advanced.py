from __future__ import print_function
import sys

import pytest
from makefun import wraps

from decopatch import function_decorator, DECORATED, InvalidMandatoryArgError, class_decorator, InvalidSignatureError, \
    WRAPPED
from decopatch.utils_disambiguation import SUPPORTS_INTROSPECTION

try:  # python 3.3+
    from inspect import signature
    funcsigs_used = False
except ImportError:
    from funcsigs import signature
    funcsigs_used = True


@pytest.mark.parametrize('nested_mode', [True, False], ids="nested_mode={}".format)
@pytest.mark.parametrize('uses_introspection', [
    pytest.param(True, marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
    False
], ids="uses_introspection={}".format)
def test_doc_impl_first_tag_mandatory(uses_introspection, nested_mode):
    """ The first implementation-first example in the doc """

    if nested_mode:
        @function_decorator(enable_stack_introspection=uses_introspection)
        def add_tag(tag):
            """
            This decorator adds the 'my_tag' tag on the decorated function,
            with the value provided as argument

            :param tag: the tag value to set
            :param f: represents the decorated item. Automatically injected.
            :return:
            """

            def replace_f(f):
                setattr(f, 'my_tag', tag)
                return f

            return replace_f
    else:
        @function_decorator(enable_stack_introspection=uses_introspection)
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

    err_type = TypeError if uses_introspection else InvalidMandatoryArgError
    with pytest.raises(err_type):
        # add_tag() missing 1 required positional argument: 'tag'
        @add_tag
        def foo():
            if True:
                return

    if not uses_introspection:
        with pytest.raises(InvalidMandatoryArgError):
            # first argument is a callable > problem
            @add_tag(print)
            def foo():
                return
    else:
        # no problem
        @add_tag(print)
        def foo():
            return

        assert foo.my_tag == print


def test_doc_impl_first_tag_optional():
    """ The second implementation-first example in the doc """

    @function_decorator
    def add_tag(tag='tag!', f=DECORATED):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :param f: represents the decorated item. Automatically injected.
        :return:
        """
        setattr(f, 'my_tag', tag)
        return f

    @add_tag('hello')  # normal arg
    def foo():
        return

    assert foo.my_tag == 'hello'

    @add_tag(tag='hello')  # normal kwarg
    def foo():
        return

    assert foo.my_tag == 'hello'

    @add_tag  # no parenthesis
    def foo():
        return

    assert foo.my_tag == 'tag!'

    @add_tag()  # empty parenthesis
    def foo():
        return

    assert foo.my_tag == 'tag!'

    # callable as first arg should be rejected but cant
    # @add_tag(print)
    # def foo():
    #     return
    #
    # assert foo.my_tag == print
    with pytest.raises(AttributeError):
        add_tag(print)

    uses_trick = not funcsigs_used
    if uses_trick:
        @add_tag(tag=print)  # callable as first kwarg works thanks to the trick
        def foo():
            return

        assert foo.my_tag == print
    else:
        with pytest.raises(AttributeError):
            add_tag(tag=print)


def test_doc_impl_first_say_hello(capsys):
    """The second implementation-first example in the doc"""

    @function_decorator
    def say_hello(person='world', f=DECORATED):
        """
        This decorator modifies the decorated function so that a nice hello
        message is printed before the call.

        :param person: the person name in the print message. Default = "world"
        :param f: represents the decorated item. Automatically injected.
        :return: a modified version of `f` that will print a hello message before executing
        """

        # create a wrapper of f that will do the print before call
        # we rely on `makefun.wraps` to preserve signature
        @wraps(f)
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
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """hello, world !
hello, world !
hello, you !
Help on function say_hello in module tests.test_doc_advanced:

say_hello(person='world')
    This decorator modifies the decorated function so that a nice hello
    message is printed before the call.
    
    :param person: the person name in the print message. Default = "world"
    :param f: represents the decorated item. Automatically injected.
    :return: a modified version of `f` that will print a hello message before executing

Signature: (person='world')
"""

    assert captured.err == ""


@pytest.mark.parametrize('uses_introspection', [
    pytest.param(True, marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
    False
], ids="uses_introspection={}".format)
def test_doc_impl_first_class_tag_mandatory(uses_introspection):
    """ The first implementation-first example in the doc """

    @class_decorator(enable_stack_introspection=uses_introspection)
    def add_tag(tag, c=DECORATED):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :param c: represents the decorated item. Automatically injected.
        :return:
        """
        setattr(c, 'my_tag', tag)
        return c

    @add_tag('hello')
    class Foo(object):
        pass

    assert Foo.my_tag == 'hello'

    err_type = InvalidMandatoryArgError  # if not uses_introspection else TypeError
    with pytest.raises(err_type):
        # add_tag() missing 1 required positional argument: 'tag'
        @add_tag
        class Foo(object):
            def __init__(self):
                if True:
                    pass

            def blah(self):
                pass

    if not uses_introspection:
        with pytest.raises(InvalidMandatoryArgError):
            # first argument is a class > problem
            @add_tag(object)
            class Foo(object):
                pass
    else:
        # no problem
        @add_tag(object)
        class Foo(object):
            pass

        assert Foo.my_tag == object


def test_doc_nested_mode_tag_mandatory():
    @function_decorator
    def add_tag(tag):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :param f: represents the decorated item. Automatically injected.
        :return:
        """

        def replace_f(f):
            setattr(f, 'my_tag', tag)
            return f

        return replace_f


# ----------- more complex / other tests derived from the above for the advanced section

@pytest.mark.parametrize('with_star', [True], ids="kwonly={}".format)
@pytest.mark.parametrize('uses_introspection', [True, False], ids="uses_introspection={}".format)
def test_doc_impl_first_tag_mandatory_protected(with_star, uses_introspection):
    if with_star:
        if sys.version_info < (3, 0):
            pytest.skip("test skipped in python 2.x because kw only is not syntactically correct")
        else:
            from ._test_doc_py3 import create_test_doc_impl_first_tag_mandatory_protected_with_star
            add_tag = create_test_doc_impl_first_tag_mandatory_protected_with_star(uses_introspection)
    else:
        raise NotImplementedError()

    @add_tag(tag='hello')
    def foo():
        return

    assert foo.my_tag == 'hello'

    with pytest.raises(TypeError):
        # add_tag() missing 1 required positional argument: 'tag'
        @add_tag
        def foo():
            return

    @add_tag(tag=print)
    def foo():
        return

    assert foo.my_tag == print


@pytest.mark.parametrize('with_star', [False, True], ids="kwonly={}".format)
def test_doc_impl_first_tag_optional_nonprotected(with_star):
    """Tests that an error is raised when nonprotected code is created """
    # with pytest.raises(AmbiguousDecoratorDefinitionError):
    if with_star:
        if sys.version_info < (3, 0):
            pytest.skip("test skipped in python 2.x because kw only is not syntactically correct")
        else:
            from ._test_doc_py3 import create_test_doc_impl_first_tag_optional_nonprotected_star
            add_tag = create_test_doc_impl_first_tag_optional_nonprotected_star()
    else:
        @function_decorator
        def add_tag(tag='tag!', f=DECORATED):
            """
            This decorator adds the 'my_tag' tag on the decorated function,
            with the value provided as argument

            :param tag: the tag value to set
            :param f: represents the decorated item. Automatically injected.
            :return:
            """
            setattr(f, 'my_tag', tag)
            return f

    @add_tag(tag='hello')
    def foo():
        return

    assert foo.my_tag == 'hello'

    @add_tag
    def foo():
        return

    assert foo.my_tag == 'tag!'


@pytest.mark.parametrize('with_star', [False, True], ids="kwonly={}".format)
@pytest.mark.parametrize('uses_introspection', [
    pytest.param(True, marks=pytest.mark.skipif(not SUPPORTS_INTROSPECTION, reason="not available on python 3.8+")),
    False
], ids="introspection={}".format)
def test_doc_impl_first_tag_optional_protected(with_star, uses_introspection):
    """ The second implementation-first example in the doc """

    if with_star:
        if sys.version_info < (3, 0):
            pytest.skip("test skipped in python 2.x because kw only is not syntactically correct")
        else:
            from ._test_doc_py3 import create_test_doc_impl_first_tag_optional_protected
            add_tag = create_test_doc_impl_first_tag_optional_protected(uses_introspection)
    else:
        # protect it explicitly if introspection is disabled
        @function_decorator(enable_stack_introspection=uses_introspection)
        def add_tag(tag='tag!', f=DECORATED):
            """
            This decorator adds the 'my_tag' tag on the decorated function,
            with the value provided as argument

            :param tag: the tag value to set
            :param f: represents the decorated item. Automatically injected.
            :return:
            """
            setattr(f, 'my_tag', tag)
            return f

    @add_tag(tag='hello')
    def foo():
        return

    assert foo.my_tag == 'hello'

    @add_tag
    def foo():
        return

    assert foo.my_tag == 'tag!'

    uses_signature_trick = not funcsigs_used
    if with_star or uses_introspection or uses_signature_trick:
        # when we add the star, disambiguation always works (even without introspection
        @add_tag(tag=print)
        def foo():
            return

        assert foo.my_tag == print
    else:
        # when we do not add the star and no introspection is used and we do not use the trick, there is a problem
        with pytest.raises(AttributeError):
            @add_tag(tag=print)
            def foo():
                return

    if not uses_introspection:
        with pytest.raises(AttributeError):
            @add_tag(print)
            def foo():
                return
    elif with_star:
        with pytest.raises(TypeError):
            @add_tag(print)
            def foo():
                return
    else:
        @add_tag(print)
        def foo():
            return

        assert foo.my_tag == print


def test_varpos_and_decorated_before_in_flat_mode():
    """
    Tests that an error is correctly raised if the decorator implementation does not make it possible for the
    injected args to be injected in flat and double-flat modes.
    """

    @function_decorator
    def foo(func=DECORATED, *tags):
        assert tags == ('hello', )

    @foo('hello')
    def f():
        pass

    @function_decorator
    def foo(func=WRAPPED, *tags):
        assert tags == ('hello', )

    @foo('hello')
    def f():
        pass

    if sys.version_info >= (3, 0):
        from ._test_doc_py3 import create_test_wrapped_bad_signature

        foo = create_test_wrapped_bad_signature(0, 'hello')

        @foo('hello')
        def f():
            pass

        for i in range(1, 4):
            with pytest.raises(InvalidSignatureError):
                create_test_wrapped_bad_signature(i, 'hello')


def test_kwargs():
    """
    Tests that we support a case where there are variable-length arguments in the decorator signature in flat mode.
    """
    @function_decorator
    def foo_deco(fixture_func=DECORATED,
                 **kwargs):
        return fixture_func

    @foo_deco
    def foo():
        pass

    foo()
