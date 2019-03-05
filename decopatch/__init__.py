from decopatch.main import function_decorator, class_decorator, decorator, FirstArgDisambiguation, \
    AmbiguousFirstArgumentTypeError, InvalidMandatoryArgError, AmbiguousDecoratorDefinitionError
from decopatch.utils_signatures import DECORATED, WRAPPED, F_ARGS, F_KWARGS

__all__ = [
    # submodules
    'main', 'utils_signatures',
    # symbols
    'function_decorator', 'class_decorator', 'decorator', 'DECORATED', 'WRAPPED', 'F_ARGS', 'F_KWARGS',
    'FirstArgDisambiguation', 'AmbiguousFirstArgumentTypeError', 'InvalidMandatoryArgError',
    'AmbiguousDecoratorDefinitionError'
]
