from decopatch.utils_disambiguation import disambiguate_using_introspection, FirstArgDisambiguation
from decopatch.utils_modes import SignatureInfo

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


def test_signature_trick():
    sig_info = SignatureInfo(signature(test_signature_trick))
    sig_info.use_signature_trick = True
    raise Exception("use signature trick = %s" % sig_info.use_signature_trick)


def test_on_functions():

    def level1():
        return disambiguate_using_introspection(3)

    def my_decorator(arg):
        my_decorator.res = level1()
        if my_decorator.res is FirstArgDisambiguation.is_decorated_target:
            return "replacement"
        elif my_decorator.res is FirstArgDisambiguation.is_normal_arg:
            def _apply(f):
                return "replacement"
            return _apply
        else:
            raise Exception()

    # trying to use the trick to see if that perturbates the introspection
    my_decorator.__wrapped__ = level1

    @my_decorator
    def foo():
        pass

    assert my_decorator.res == FirstArgDisambiguation.is_decorated_target

    @my_decorator(foo)
    def foo():
        pass

    assert my_decorator.res == FirstArgDisambiguation.is_normal_arg
