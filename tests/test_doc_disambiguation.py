from __future__ import print_function

import sys

import pytest

from decopatch import decorator, DECORATED


@pytest.mark.parametrize('flat_mode', [False, True], ids="flat_mode={}".format)
def test_no_args(capsys, flat_mode):
    """ Tests that the no-args example works in both modes """

    if not flat_mode:
        @decorator
        def replace_with_hello():
            """
            Decorator to replace anything with the 'hello' string.
            """
            def _apply_decorator(f):
                return 'hello'
            return _apply_decorator
    else:
        @decorator
        def replace_with_hello(f=DECORATED):
            """
            Decorator to replace anything with the 'hello' string.
            """
            return 'hello'

    with capsys.disabled():
        help(replace_with_hello)

    help(replace_with_hello)

    with capsys.disabled():
        @replace_with_hello
        def foo():
            pass

        assert foo == 'hello'

        @replace_with_hello()
        def foo():
            pass

        assert foo == 'hello'

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == """Help on function replace_with_hello in module tests.test_doc_disambiguation:

replace_with_hello(*_)
    Decorator to replace anything with the 'hello' string.

"""

    with capsys.disabled():
        assert replace_with_hello(print) == 'hello'

        with pytest.raises(TypeError):
            replace_with_hello(1)

        with pytest.raises(TypeError):
            replace_with_hello(1, 2)


@pytest.mark.parametrize('flat_mode', [False, True], ids="flat_mode={}".format)
def test_mandatory_kwargs(flat_mode):
    """ Tests that the no-args example works in both modes """

    if sys.version_info < (3, 0):
        pytest.skip("test skipped in python 2.x because kw-only is not syntactically correct")
    else:
        from ._test_doc_py3 import create_test_doc_disambiguation_kwonly_mandatory
        replace_with = create_test_doc_disambiguation_kwonly_mandatory(flat_mode)

    help(replace_with)

    @replace_with(replacement='hello')
    def foo():
        pass
    assert foo == 'hello'

    with pytest.raises(TypeError):
        replace_with(1)

    with pytest.raises(TypeError):
        replace_with(print)


@pytest.mark.parametrize('flat_mode', [False, True], ids="flat_mode={}".format)
def test_optional_kwargs(flat_mode):
    """ Tests that the no-args example works in both modes """

    if sys.version_info < (3, 0):
        pytest.skip("test skipped in python 2.x because kw-only is not syntactically correct")
    else:
        from ._test_doc_py3 import create_test_doc_disambiguation_kwonly_optional
        replace_with = create_test_doc_disambiguation_kwonly_optional(flat_mode)

    help(replace_with)

    @replace_with
    def foo():
        pass
    assert foo == 'hello'

    @replace_with(replacement='foo')
    def foo():
        pass
    assert foo == 'foo'

    with pytest.raises(TypeError):
        replace_with(1)  # TypeError: replace_with() takes 0 positional arguments but 1 positional argument (and 1 keyword-only argument) were given

    # problem...
    replace_with(print)
