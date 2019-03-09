from __future__ import print_function

from decopatch import function_decorator, WRAPPED, F_ARGS, F_KWARGS


def test_so1():
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
