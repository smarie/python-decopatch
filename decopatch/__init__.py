from decopatch.main import function_decorator, class_decorator, decorator, FirstArgDisambiguation, \
    AmbiguousFirstArgumentTypeError, InvalidMandatoryArgError, AmbiguousDecoratorDefinitionError
from decopatch.utils_signatures import DECORATED

__all__ = [
    # submodules
    'main', 'utils_signatures',
    # symbols
    'function_decorator', 'class_decorator', 'decorator', 'DECORATED', 'FirstArgDisambiguation',
    'AmbiguousFirstArgumentTypeError', 'InvalidMandatoryArgError', 'AmbiguousDecoratorDefinitionError'
]
