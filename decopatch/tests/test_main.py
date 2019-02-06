from decopatch import decorator, DECORATED


def test_no_arg():

    # put your breakpoints here :)
    print()

    def foo():
        pass

    @decorator()
    def replace_by_foo(f=DECORATED):
        return foo

    @replace_by_foo
    def bar():
        pass

    assert bar is foo

    @replace_by_foo()
    def bar():
        pass

    assert bar is foo


def test_var_positional():
    # put your breakpoints here :)
    print()

    def foo():
        pass

    @decorator()
    def replace_by_foo(*args, f=DECORATED):
        return foo

    @replace_by_foo
    def bar():
        pass

    assert bar is foo

    @replace_by_foo()
    def bar():
        pass

    assert bar is foo
