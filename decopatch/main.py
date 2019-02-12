from enum import Enum
from inspect import isclass

from makefun import with_signature, remove_signature_parameters, add_signature_parameters

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


def function_decorator(decorator_function):
    """
    A decorator to create function decorators.
    Equivalent to

    decorator(is_function_decorator=True, is_class_decorator=False, can_first_arg_be_ambiguous=False)

    :param decorator_function:
    :return:
    """
    return decorator(is_function_decorator=True, is_class_decorator=False, can_first_arg_be_ambiguous=False)(decorator_function)


def class_decorator(decorator_function):
    """
    A decorator to create class decorators
    Equivalent to

    decorator(is_function_decorator=False, is_class_decorator=True, can_first_arg_be_ambiguous=False)

    :param decorator_function:
    :return:
    """
    return decorator(is_function_decorator=False, is_class_decorator=True, can_first_arg_be_ambiguous=False)(decorator_function)


class DECORATED:
    """A symbol used in you implementation-first signatures to declare where the decorated object should be injected"""
    pass


class FirstArgDisambiguation(Enum):
    """
    This enum is used for the output of user-provided first argument disambiguators.
    """
    is_positional_arg = 0
    is_decorated_target = 1
    is_ambiguous = 2


def decorator(is_function_decorator=True,                   # type: bool
              is_class_decorator=True,                      # type: bool
              can_first_arg_be_ambiguous=True,              # type: bool
              callable_or_cls_firstarg_disambiguator=None,  # type: Callable
              wraps=None,                                   # type: str
              ):
    """
    A decorator to create decorators.

    It support two modes: "implementation-first", and "usage-first".

    In "implementation-first" mode your implementation is flat:

    ```python
    def my_decorator(a, b, f=DECORATED):
        # ...
        return <replacement for f>
    ```

    For "implementation-first" mode to be automatically detected, your implementation has to have an argument with
    default value DECORATED. This argument will be injected with the decorated target when you rdecorator is used.
    Alternately you can explicitly provide the injected argument name by specifying a non-None `wraps` argument.

    In any other case the "usage-first" mode is activated. In this mode your implementation is nested:

    ```python
    def my_decorator(a, b):
        def replace_f(f):
            # ...
            return <replacement for f>
        return replace_f
    ```

    In both modes, because python language does not redirect no-parenthesis usages (@my_decorator) to no-args usages
    (@my_decorator()), there is a need for disambiguation in some cases.

    The default behaviour is the following:
     - if your function has 0 arguments, everything works as expected. Your decorator can be used with and without
     parenthesis, this will lead to the same call to your implementation function.

     TODO continue

    :param is_function_decorator:
    :param is_class_decorator:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:

    :return:
    """

    if callable(is_function_decorator):
        # called without argument: the first argument is actually the decorated function
        f = is_function_decorator
        return create_decorator(f)
    else:
        # called with argument
        def deco(d):
            return create_decorator(d,
                                    is_function_decorator=is_function_decorator,
                                    is_class_decorator=is_class_decorator,
                                    can_first_arg_be_ambiguous=can_first_arg_be_ambiguous,
                                    callable_or_cls_firstarg_disambiguator=callable_or_cls_firstarg_disambiguator,
                                    wraps=wraps)
        return deco


def create_decorator(decorator_function,
                     is_function_decorator=True,                   # type: bool
                     is_class_decorator=True,                      # type: bool
                     can_first_arg_be_ambiguous=True,              # type: bool
                     callable_or_cls_firstarg_disambiguator=None,  # type: Callable
                     wraps=None,                                   # type: str
                     ):
    """
    Creates a decorator from the `decorator_function` implementation.

    :param decorator_function:
    :param is_function_decorator:
    :param is_class_decorator:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:
    :param wraps:
    :return:
    """

    if not is_function_decorator and not is_class_decorator:
        raise ValueError("At least one of `is_function_decorator` and `is_class_decorator` must be True")

    # create the disambiguator (TODO check if we need it in usage-first mode too ?)
    def disambiguator(callable_or_cls_first_arg):
        # we want to eliminate as much as possible the args that cannot be first args
        if callable(callable_or_cls_first_arg) and not is_function_decorator:
            return FirstArgDisambiguation.is_decorated_target
        elif isclass(callable_or_cls_first_arg) and not is_class_decorator:
            return FirstArgDisambiguation.is_decorated_target
        elif callable_or_cls_firstarg_disambiguator is not None:
            return callable_or_cls_firstarg_disambiguator(callable_or_cls_first_arg)
        elif can_first_arg_be_ambiguous:
            return FirstArgDisambiguation.is_ambiguous
        else:
            # user set 'can_first_arg_be_ambiguous' to false
            return FirstArgDisambiguation.is_decorated_target

    # extract the implementation's signature
    ds = signature(decorator_function)

    # determine the mode (impl-first or not)
    if wraps is not None:
        # validate that the 'wraps' parameter is a string representing a real parameter of the function
        if not isinstance(wraps, str):
            raise TypeError("'wraps' argument should be a string with the argument name where the wrapped object "
                            "should be injected")
        if wraps not in ds.parameters:
            return ValueError("Function '%s' does not have an argument named '%s'"
                              "" % (decorator_function.__name__, wraps))
    else:
        # let's check the signature
        wraps, wraps_p = get_decorated_parameter(ds)

    # if there is a parameter with default=DECORATED or an explicit 'wraps' argument, that's an impl-first mode
    if wraps is not None:
        return make_implementation_first_decorator(decorator_function, ds, wraps,
                                                   first_arg_disambiguator=disambiguator)
    else:
        return make_usage_first_decorator(decorator_function, ds)


def make_implementation_first_decorator(decorator_function,
                                        ds,
                                        injected_arg_name,
                                        first_arg_disambiguator):
    """
    Creates a decorator, based on the implementation_first `decorator_function`.

    :param decorator_function:
    :param ds:
    :param injected_arg_name: the name of the argument in the decorator function, that should be injected by us.
    :param first_arg_disambiguator:
    :return:
    """
    # create the signature of the decorator function = the same signature but we remove the injected arg.
    new_ds = remove_signature_parameters(ds, injected_arg_name)

    # check if the resulting function has any parameter at all
    if len(new_ds.parameters) == 0:
        # (A) no argument at all. Special handling. We create a function with var-args and check the length.
        @with_signature(None,
                        func_name=decorator_function.__name__,
                        doc=decorator_function.__doc__,
                        modulename=decorator_function.__module__)
        def new_decorator(*args):
            if len(args) == 0:
                # called with no args BUT parenthesis: @foo_decorator().
                # we have to return a nested function to apply the decorator
                def decorate(f):
                    # use a keyword way so as to handle keyword-only cases
                    kw = {injected_arg_name: f}
                    return decorator_function(**kw)
                return decorate

            elif len(args) == 1:
                # called with no arg NOR parenthesis: @foo_decorator
                # we have to directly apply the decorator
                kw = {injected_arg_name: args[0]}
                return decorator_function(**kw)
            else:
                # more than 1 argument: not possible
                raise TypeError("Decorator function '%s' does not accept any argument."
                                "" % decorator_function.__name__)
    else:
        # (B) general case: at least one argument

        # get information about the first argument
        name_first_arg, first_sig_param = get_first_parameter(new_ds)
        # type_hint = get_type_hint(p) if p is not None else None
        first_arg_kind = first_sig_param.kind if first_sig_param is not None else None
        is_first_arg_varpositional = first_arg_kind is Parameter.VAR_POSITIONAL
        is_first_arg_mandatory = first_sig_param.default is first_sig_param.empty and not is_first_arg_varpositional

        if first_arg_kind in {Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD}:
            # The first argument CANNOT be positional, so `@new_decorator` cannot be used without parenthesis
            # (it would raise an exception).
            no_parenthesis_calls_are_impossible = True
        else:
            no_parenthesis_calls_are_impossible = False

        @with_signature(new_ds,
                        func_name=decorator_function.__name__,
                        doc=decorator_function.__doc__,
                        modulename=decorator_function.__module__)
        def new_decorator(*args, **kwargs):

            # # There is a possibility that the caller sent a single argument (even if we see more here
            # # because the defaults have been added by with_signature), and that it results from a non-parenthesis use.
            # if len(args) >= 1:
            #     # (3) because of the way `@with_signature` works as of today, this can only happen if the
            #     # decorator signature has a positional-only (not possible in python today)
            #     # or a var-positional argument.
            #     name_of_first_arg_received = name_first_arg
            #     first_arg_received = args[0]
            # else:
            #     # (4) normal case, almost all cases fall here (because `@with_signature` redirect all to kw)
            #     # unfortunately because our decorator preserves signature, we always receive all arguments,
            #     # in the order defined in the signature.
            #     # -so as of today there is no way that this line returns the actual first argument provided:
            #     # name_of_first_arg_received, first_arg_received = next(iter(kwargs.items()))
            #     # -the only thing that works is this
            #     name_of_first_arg_received = name_first_arg
            #     first_arg_received = kwargs[name_first_arg]

            if no_parenthesis_calls_are_impossible:
                used_without_parenthesis = False
            else:
                # since we expose a decorator with a preserved signature and not (*args, **kwargs)
                # we lose the information about the number of arguments *actually* provided.
                # we may receive several args and kwargs if there are optional arguments (even if user did not provide
                # them) so let's try to eliminate some cases by looking at the default/nondefault

                bound = new_ds.bind(*args, **kwargs)

                # get the first positional arg's value.
                if is_first_arg_varpositional and name_first_arg not in bound.arguments:
                    # this seems to happen at least in python 3.5 but is it the case in all other cases ?
                    used_without_parenthesis = False
                else:
                    first_positional_arg_value = bound.arguments[name_first_arg]

                    # handle var-positional
                    is_var_positional_and_empty = True
                    if is_first_arg_varpositional:
                        if len(first_positional_arg_value) > 0:
                            first_positional_arg_value = first_positional_arg_value[0]
                        else:
                            is_var_positional_and_empty = False

                    if is_var_positional_and_empty \
                            and is_no_parenthesis_call_possible_from_args_values(new_ds, bound, name_first_arg) \
                            and can_arg_be_a_decorator_target(first_positional_arg_value):
                        # at this point our first positional arg
                        # - is different from its default value (and that's the only one)
                        # - is a callable or class.
                        # So a no-parenthesis call is still possible... we have to disambiguate now
                        result = disambiguate_single_arg_callable_or_class(first_positional_arg_value,
                                                                                             decorator_function,
                                                                                             name_first_arg,
                                                                                             is_first_arg_mandatory,
                                                                                             is_first_arg_varpositional,
                                                                                             first_arg_disambiguator)

                        if result is FirstArgDisambiguation.is_decorated_target:
                            used_without_parenthesis = True
                        elif result is FirstArgDisambiguation.is_positional_arg:
                            used_without_parenthesis = False
                        else:
                            raise ValueError("single-argument disambiguation did not return properly: received %s" % result)

                    else:
                        # we are sure that a no-parenthesis call is not possible
                        used_without_parenthesis = False

            if used_without_parenthesis:
                # @foo_decorator
                # we have to directly apply the decorator
                kw = {injected_arg_name: first_positional_arg_value}
                return decorator_function(**kw)
            else:
                # @foo_decorator(a).
                # we have to return a nested function to apply the decorator
                def decorate(f):
                    # inject the decorated item in the keyword arguments
                    kwargs[injected_arg_name] = f
                    return decorator_function(*args, **kwargs)
                return decorate

    return new_decorator


def is_no_parenthesis_call_possible_from_args_values(new_ds, bound, name_first_arg):
    """
    Returns False if we are absolutely certain that this is not a no-parenthesis call. this can be
    - if >=2 arguments have values different from their default values are present,
    - if 0 arguments are different from their default values.
    - if 1 argument has a different value from its default value, but it is not the first one.

    Indeed when there is a non-parenthesis call,
    - only one argument is provided, not more
    - and this argument has a value that is necessarily different from the default, because it is something that did
    not exist when the decorator implementer was created.

    So, in other words, the only case where True is returned is when **ONLY the first argument has a non-default value**

    :param new_ds:
    :param bound: obtained from signature.bind(*args, **kwargs)
    :param name_first_arg: the name of the first positional argument
    :return:
    """
    # if the first positional argument has NOT been set, we are sure that's not a no-parenthesis call
    if bound.arguments[name_first_arg] is new_ds.parameters[name_first_arg].default:
        return False

    else:
        # check if there are 0, 1 or >=2 arguments that are different from their default values
        different_than_default = 0
        for p_name, p_def in new_ds.parameters.items():
            if bound.arguments[p_name] is not p_def.default:
                different_than_default += 1
            if different_than_default >= 2:
                break

        # if all are default then it is not possible that the decorated object is in here
        # if more than 1 is default then 2 explicit arguments have necessarily be provided
        return different_than_default == 1


def can_arg_be_a_decorator_target(arg):
    """
    Returns True if the argument received has a type that can be decorated.

    If this method returns False, we are sure that this is a *with*-parenthesis call
    because python does not allow you to decorate anything else than a function or a class

    :param arg:
    :return:
    """
    return callable(arg) or isclass(arg)


class AmbiguousFirstArgumentTypeError(TypeError):
    pass


class InvalidMandatoryArgError(TypeError):
    pass


def disambiguate_single_arg_callable_or_class(first_arg_received,
                                              decorator_function,
                                              name_first_arg,
                                              is_first_arg_mandatory,
                                              is_first_arg_varpositional,
                                              first_arg_disambiguator):
    """

    :param first_arg_received:
    :return:
    """
    if is_first_arg_varpositional:
        name_first_arg_for_msg = '*' + name_first_arg
    else:
        name_first_arg_for_msg = name_first_arg

    # rely on the provided handler
    res = first_arg_disambiguator(first_arg_received)

    if res is FirstArgDisambiguation.is_ambiguous:
        # default implementation: very conservative
        if is_first_arg_mandatory:
            # the function does not accept to be called without arguments, and the first cannot be a callable/class
            # so that has to be an error
            raise AmbiguousFirstArgumentTypeError(
                "function '%s' requires a mandatory argument '%s'. It cannot be a class nor a callable."
                " If you think that it should, then ask your decorator provider to protect his decorator (see decopath "
                "documentation)" % (decorator_function.__name__, name_first_arg_for_msg))
        else:
            # the first argument is optional and received a callable or a class.
            raise AmbiguousFirstArgumentTypeError(
                "Argument '%s' of generated decorator function '%s' is the *first* argument in the signature. "
                "When the decorator is called (1) with only this argument as non-default value and (2) if this argument"
                " is a callable or class, then it is not possible to determine if that call was a "
                "no-parenthesis decorator usage or a with-args decorator usage. If you think that this particular usage"
                " should be allowed, then ask your decorator provider to protect his decorator (see decopath "
                "documentation)" % (name_first_arg_for_msg, decorator_function.__name__))

    elif res is FirstArgDisambiguation.is_decorated_target and is_first_arg_mandatory:
        # that's not possible
        raise InvalidMandatoryArgError("function '%s' requires a mandatory argument '%s'. Provided value '%s' does "
                                       "not pass its validation criteria" % (decorator_function.__name__,
                                                                             name_first_arg_for_msg,
                                                                             first_arg_received))
    else:
        return res


    # else:
    #     if is_first_arg_varpositional:
    #         # all arguments are optional and the first is variable-length positional.
    #         raise Exception()
    #     else:
        #     # all arguments are optional and the first can be non-keyword-based.
        #     if is_invalid_first_arg is not None and is_invalid_first_arg(first_arg_received):
        #         # the function tells us that this argument can not be
        #
        #         # default = not callable(first_arg_received) and not isclass(first_arg_received)
        #         # the disambiguator tells us that this can not be a decorated target
        #         was_used_without_parenthesis = False
        #
        #     else:
        #         # !!!! THIS IS A NO-PARENTHESIS CALL !!!!
        #         was_used_without_parenthesis = True
            # !!!! THIS IS A NO-PARENTHESIS CALL !!!!
            # return True


def make_usage_first_decorator(decorator_function, ds):
    """

    :param decorator_function:
    :param ds:
    :return:
    """
    ds_has_no_mandatory_arg = has_no_mandatory_arg(ds)

    def new_decorator(*args, **kwargs):

        # Detect if the decorator was used without argument
        if ds_has_no_mandatory_arg and len(args) == 1 and len(kwargs) == 0:
            # in that case a single arg is there = the target
            target = args[0]

            # let's try to build the combined decorator for 'no argument'
            sub_decorators = decorator_function()
            cd = generate_combined_decorator(target_filters, sub_decorators)

            # apply it
            try:
                return cd(target)
            except TargetNotCompliantException:
                # ignore, maybe the target is an argument for the decorator
                pass

        # Otherwise, if we're here then the args are for the decorator constructor.
        sub_decorators = decorator_function(*args, **kwargs)
        return generate_combined_decorator(target_filters, sub_decorators)

    return new_decorator


def has_no_mandatory_arg(ds  # type: Signature
                         ):
    """
    Returns
    :param ds:
    :return:
    """
    at_least_one_mandatory_arg = False
    for p_name, p_def in ds.parameters.items():
        if p_def.default is ds.empty and \
                not p_def.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
            at_least_one_mandatory_arg = True
            break

    return not at_least_one_mandatory_arg


def get_decorated_parameter(ds  # type: Signature
                            ):
    """
    Returns the (name, Parameter) for the parameter with default value DECORATED

    :param ds:
    :return:
    """
    for p_name, p in ds.parameters.items():
        if p.default is DECORATED:
            return p_name, p

    # not found
    return None, None


def get_first_parameter(ds  # type: Signature
                        ):
    """
    Returns the (name, Parameter) for the first parameter in the signature

    :param ds:
    :return:
    """
    try:
        return next(iter(ds.parameters.items()))
    except StopIteration:
        return None, None


# def get_type_hint(p  # type: Parameter
#                   ):
#     if p.annotation is p.empty:
#         return None
#     else:
#         return p.annotation


class TargetNotCompliantException(Exception):
    pass


def generate_combined_decorator(target_filters, sub_decorators):
    """
    Generates a combined decorator from a tuple of filters and a tuple of decorators.

    :param target_filters:
    :param sub_decorators:
    :return:
    """
    try:
        if len(target_filters) != len(sub_decorators):
            raise ValueError("Number of returned sub-decorators is not the same as the number of target filters")
    except TypeError:
        if len(target_filters) != 1:
            raise ValueError("Only one returned sub-decorator but the number of target filters is %s"
                             "" % len(target_filters))
        sub_decorators = [sub_decorators]

    def combined_decorator(target):
        # lets see if it is a valid target and use the appropriate decorator if so
        for i, (filter_, decorator_to_use) in enumerate(zip(target_filters, sub_decorators)):
            if filter_(target):
                # valid target ! so the decorator is most probably used without argument
                # let's find the appropriate sub-decorator and apply it
                return decorator_to_use(target)

        raise TargetNotCompliantException("decorated object does is not compliant with the filters")

    return combined_decorator
