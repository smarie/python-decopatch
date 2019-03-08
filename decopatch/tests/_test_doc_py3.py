from decopatch import function_decorator, DECORATED, decorator


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
