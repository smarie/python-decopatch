from decopatch import function_decorator, DECORATED, decorator, F_ARGS, F_KWARGS, WRAPPED


def create_test_doc_impl_first_tag_mandatory_protected_with_star(uses_introspection):

    @function_decorator(enable_stack_introspection=uses_introspection)
    def add_tag(*, tag, f=DECORATED):
        setattr(f, 'my_tag', tag)
        return f

    return add_tag


def create_test_doc_impl_first_tag_optional_nonprotected_star():
    """Tests that an error is raised when nonprotected code is created """

    @function_decorator
    def add_tag(*, tag='tag!'):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :return:
        """
        def _apply_on(f):
            setattr(f, 'my_tag', tag)
            return f
        return _apply_on

    return add_tag


def create_test_doc_impl_first_tag_optional_protected(uses_introspection):
    """ The second implementation-first example in the doc """

    # protect it explicitly if introspection is disabled
    @function_decorator(enable_stack_introspection=uses_introspection)
    def add_tag(*, tag='tag!', f=DECORATED):
        """
        This decorator adds the 'my_tag' tag on the decorated function,
        with the value provided as argument

        :param tag: the tag value to set
        :param f: represents the decorated item. Automatically injected.
        :return:
        """
        setattr(f, 'my_tag', tag)
        return f

    return add_tag


def create_test_wrapped_bad_signature(test_nb, *ref_tags):
    """

    :param test_nb:
    :return:
    """
    if test_nb == 0:
        @function_decorator
        def foo(func=WRAPPED, *tags, f_args=F_ARGS, f_kwargs=F_KWARGS):
            assert tags == ref_tags
    elif test_nb == 1:
        @function_decorator
        def foo(f_args=F_ARGS, *tags, func=WRAPPED, f_kwargs=F_KWARGS):
            assert tags == ref_tags
    elif test_nb == 2:
        @function_decorator
        def foo(f_kwargs=F_KWARGS, *tags, func=WRAPPED, f_args=F_ARGS):
            assert tags == ref_tags
    elif test_nb == 3:
        @function_decorator
        def foo(f_kwargs=F_KWARGS, func=WRAPPED, *tags, f_args=F_ARGS):
            assert tags == ref_tags

    return foo

# --------- from test_doc_disambiguation.py

def create_test_doc_disambiguation_kwonly_mandatory(flat_mode):
    """ """
    if not flat_mode:
        @decorator
        def replace_with(*, replacement):
            """
            Decorator to replace anything with the <replacement> object.
            """
            def _apply_decorator(f):
                return replacement
            return _apply_decorator
    else:
        @decorator
        def replace_with(*, replacement, f=DECORATED):
            """
            Decorator to replace anything with the <replacement> object.
            """
            return replacement
    return replace_with


def create_test_doc_disambiguation_kwonly_optional(flat_mode):
    """ """
    if not flat_mode:
        @decorator
        def replace_with(*, replacement='hello'):
            """
            Decorator to replace anything with the <replacement> object.
            """
            def _apply_decorator(f):
                return replacement
            return _apply_decorator
    else:
        @decorator
        def replace_with(*, replacement='hello', f=DECORATED):
            """
            Decorator to replace anything with the <replacement> object.
            """
            return replacement
    return replace_with
