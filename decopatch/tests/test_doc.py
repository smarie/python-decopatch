from makefun import with_signature
import decopatch as dp


def test_doc_simplistic():
    """ In this test a simple function decorator is created using @dp.function_decorator. It simply sets a field on the target"""

    @dp.function_decorator
    def set_a_field(a_value):
        """Your decorator. Its signature is the one that we want users to see e.g. `@set_a_field('hello')`."""

        def replace_f(f):
            """The function that will be called at static time to replace the decorated functions"""

            # In this example we simply set an attribute on the function
            setattr(f, 'a', a_value)

            # The decorated f will be replaced by this f
            return f

        return replace_f

    @set_a_field('hello')
    def foo(a):
        pass

    assert foo.a == 'hello'


def test_doc_simple_func():
    """ In this test a function decorator is created using @dp.function_decorator. It wraps the target functions with
    an args storage """

    store = []

    @dp.function_decorator
    def save_on_access(var=store):
        """The decorator. Its signature is the one that we want users to see when they type."""

        def replace_f(f):
            """The function that will be executed to replace the decorated function"""

            # In this example we simply set an attribute on the function
            setattr(f, 'is_decorated', True)

            # In this other example we replace a function
            @with_signature(f)
            def f_wrapper(*args, **kwargs):
                # first save
                var.append((args, kwargs))
                # then call
                return f(*args, **kwargs)

            return f_wrapper

        return replace_f

    @save_on_access
    def foo(a):
        pass

    @save_on_access()
    def bar(a):
        pass

    foo(1)
    bar(2)

    assert store == [((), {'a': 1}), ((), {'a': 2})]

    store2 = []

    @save_on_access(store2)
    def bar2(a):
        pass

    bar2(3)

    assert store == [((), {'a': 1}), ((), {'a': 2})]
    assert store2 == [((), {'a': 3})]
