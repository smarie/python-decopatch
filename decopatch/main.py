from enum import Enum
from inspect import isclass, stack

from makefun import with_signature, remove_signature_parameters, add_signature_parameters
from decopatch.utils_signatures import get_decorated_parameter, get_first_parameter

try:  # python 3.3+
    from inspect import signature, Parameter, Signature
except ImportError:
    from funcsigs import signature, Parameter, Signature

try:  # python 3.5+
    from typing import Callable, Any, Optional
except ImportError:
    pass


class FirstArgDisambiguation(Enum):
    """
    This enum is used for the output of user-provided first argument disambiguators.
    """
    is_normal_arg = 0
    is_decorated_target = 1
    is_ambiguous = 2


def function_decorator(enable_stack_introspection=True,              # type: bool
                       can_first_arg_be_ambiguous=None,              # type: Optional[bool]
                       callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                       decorated=None,                                   # type: Optional[str]
                       ):
    """
    A decorator to create function decorators.
    Equivalent to

        decorator(is_function_decorator=True, is_class_decorator=False)

    :param enable_stack_introspection:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:
    :param decorated:
    :return:
    """
    if callable(enable_stack_introspection):
        # no-parenthesis call
        f = enable_stack_introspection
        return decorator(is_function_decorator=True,
                         is_class_decorator=False)(f)
    else:
        return decorator(is_function_decorator=True,
                         is_class_decorator=False,
                         enable_stack_introspection=enable_stack_introspection,
                         can_first_arg_be_ambiguous=can_first_arg_be_ambiguous,
                         callable_or_cls_firstarg_disambiguator=callable_or_cls_firstarg_disambiguator,
                         decorated=decorated)


def class_decorator(enable_stack_introspection=True,              # type: bool
                    can_first_arg_be_ambiguous=None,              # type: Optional[bool]
                    callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                    decorated=None,                                   # type: Optional[str]
                    ):
    """
    A decorator to create class decorators
    Equivalent to

        decorator(is_function_decorator=False, is_class_decorator=True)

    :param enable_stack_introspection:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:
    :param decorated:
    :return:
    """
    if callable(enable_stack_introspection):
        # no-parenthesis call
        f = enable_stack_introspection
        return decorator(is_function_decorator=False,
                         is_class_decorator=True)(f)
    else:
        return decorator(is_function_decorator=False,
                         is_class_decorator=True,
                         enable_stack_introspection=enable_stack_introspection,
                         can_first_arg_be_ambiguous=can_first_arg_be_ambiguous,
                         callable_or_cls_firstarg_disambiguator=callable_or_cls_firstarg_disambiguator,
                         decorated=decorated)


def decorator(is_function_decorator=True,                   # type: bool
              is_class_decorator=True,                      # type: bool
              enable_stack_introspection=True,              # type: bool
              can_first_arg_be_ambiguous=None,              # type: Optional[bool]
              callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
              decorated=None,                                   # type: str
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
    Alternately you can explicitly provide the injected argument name by specifying a non-None `decorated` argument.

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
    :param enable_stack_introspection:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:
    :param decorated:
    :return:
    """

    if callable(is_function_decorator):
        # called without argument: the first argument is actually the decorated function
        f = is_function_decorator
        return create_decorator(f)
    else:
        # called with argument. Return a decorator function
        def deco(f):
            return create_decorator(f,
                                    is_function_decorator=is_function_decorator,
                                    is_class_decorator=is_class_decorator,
                                    enable_stack_introspection=enable_stack_introspection,
                                    can_first_arg_be_ambiguous=can_first_arg_be_ambiguous,
                                    callable_or_cls_firstarg_disambiguator=callable_or_cls_firstarg_disambiguator,
                                    decorated=decorated)
        return deco


class AmbiguousDecoratorDefinitionError(Exception):
    pass


def create_decorator(decorator_function,
                     is_function_decorator=True,                   # type: bool
                     is_class_decorator=True,                      # type: bool
                     enable_stack_introspection=True,              # type: bool
                     can_first_arg_be_ambiguous=None,              # type: Optional[bool]
                     callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                     decorated=None,                                   # type: Optional[str]
                     ):
    """
    Main function to create a decorator implemented with the `decorator_function` implementation.

    :param decorator_function:
    :param is_function_decorator:
    :param is_class_decorator:
    :param enable_stack_introspection:
    :param can_first_arg_be_ambiguous:
    :param callable_or_cls_firstarg_disambiguator:
    :param decorated:
    :return:
    """
    # input checks
    if not is_function_decorator and not is_class_decorator:
        raise ValueError("At least one of `is_function_decorator` and `is_class_decorator` must be True")

    # (1) --- Detect mode and prepare signature to generate --------
    # extract the implementation's signature
    implementors_signature = signature(decorator_function)

    # determine the mode (impl-first or not)
    if decorated is not None:
        # validate that the 'decorated' parameter is a string representing a real parameter of the function
        if not isinstance(decorated, str):
            raise TypeError("'decorated' argument should be a string with the argument name where the wrapped object "
                            "should be injected")
        if decorated not in implementors_signature.parameters:
            return ValueError("Function '%s' does not have an argument named '%s'"
                              "" % (decorator_function.__name__, decorated))
    else:
        # let's check the signature
        decorated, decorated_p = get_decorated_parameter(implementors_signature)

    # if there is a parameter with default=DECORATED or an explicit 'decorated' argument, that's an impl-first mode
    is_impl_first_mode = decorated is not None
    injected_arg_name = decorated

    # create the signature of the decorator function to create
    if is_impl_first_mode:
        # --impl-first: the same signature but we remove the injected arg.
        generated_signature = remove_signature_parameters(implementors_signature, injected_arg_name)
    else:
        # --usage-first: keep the signature 'as is'
        generated_signature = implementors_signature

    # (2) --- Generate according to the situation--------
    # check if the resulting function has any parameter at all
    if len(generated_signature.parameters) == 0:
        # (A) no argument at all. Special handling.
        return create_no_args_decorator(decorator_function, is_impl_first_mode, injected_arg_name=injected_arg_name)

    else:
        # (B) general case: at least one argument - we have to get information about the first one, to handle properly
        first_arg_name, first_arg_def = get_first_parameter(generated_signature)

        # is it keyword-only ? varpositional ? mandatory ?
        first_arg_kind = first_arg_def.kind if first_arg_def is not None else None
        is_first_arg_keyword_only = first_arg_kind in {Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD}
        is_first_arg_varpositional = first_arg_kind is Parameter.VAR_POSITIONAL
        is_first_arg_mandatory = first_arg_def.default is first_arg_def.empty and not is_first_arg_varpositional

        # is our decorator protected ?
        explicitly_protected = enable_stack_introspection or can_first_arg_be_ambiguous is not None \
                               or callable_or_cls_firstarg_disambiguator is not None  # or is_first_arg_keyword_only

        if not is_first_arg_mandatory and not explicitly_protected:
            # if the decorator has all-optional arguments, we prevent it to be created if it is not protected.
            # This is because ambiguous cases ARE nominal cases, they happen all the time
            raise AmbiguousDecoratorDefinitionError("This decorator is ambiguous because it has only optional "
                                                    "arguments. Please provide an explicit protection.")
        else:
            # if the decorator has at least 1 mandatory argument, we allow it to be created but its default behaviour
            # is to raise errors only on ambiguous cases. Usually ambiguous cases are rare (not nominal cases)
            disambiguator = create_single_arg_callable_or_class_disambiguator(decorator_function,
                                                                              is_function_decorator,
                                                                              is_class_decorator,
                                                                              can_first_arg_be_ambiguous,
                                                                              callable_or_cls_firstarg_disambiguator,
                                                                              enable_stack_introspection,
                                                                              first_arg_name,
                                                                              is_first_arg_mandatory)

        if is_first_arg_keyword_only:
            # in this case the decorator *can* be used without arguments but *cannot* with one positional argument,
            # which will happen in the no-parenthesis case. We have to modify the signature to allow no-parenthesis
            return create_kwonly_decorator(generated_signature, decorator_function, disambiguator,
                                           is_impl_first_mode=is_impl_first_mode,
                                           is_first_arg_mandatory=is_first_arg_mandatory,
                                           injected_arg_name=injected_arg_name)
        elif is_first_arg_varpositional:
            # in this case the varpositional argument can be used to detect no-args and multi-args calls
            return create_varpositional_decorator(generated_signature, decorator_function, disambiguator,
                                                  is_impl_first_mode=is_impl_first_mode,
                                                  is_first_arg_mandatory=is_first_arg_mandatory,
                                                  first_arg_name=first_arg_name,
                                                  injected_arg_name=injected_arg_name)
        else:
            # general case
            return create_general_case_decorator(generated_signature, decorator_function, disambiguator,
                                                 is_impl_first_mode=is_impl_first_mode,
                                                 is_first_arg_mandatory=is_first_arg_mandatory,
                                                 first_arg_name=first_arg_name,
                                                 injected_arg_name=injected_arg_name)


def create_no_args_decorator(decorator_function,
                             is_impl_first_mode,     # type: bool
                             injected_arg_name=None  # type: str
                             ):
    """
    Utility method to create a decorator that has no arguments at all and is implemented by `decorator_function`, in
    implementation-first mode or usage-first mode.

    The created decorator is a function with var-args. When called it checks the length
    (0=called with parenthesis, 1=called without, 2=error).

    Note: we prefer to use this var-arg signature rather than a "(_=None)" signature, because it is more readable for
    the decorator's help.

    :param decorator_function:
    :param is_impl_first_mode:
    :param injected_arg_name: should be None in usage-first mode
    :return:
    """
    if (injected_arg_name is not None) != is_impl_first_mode:
        raise ValueError("`injected_arg_name` should only be non-None when `is_impl_first_mode` is True")

    @with_signature(None,
                    func_name=decorator_function.__name__,
                    doc=decorator_function.__doc__,
                    modulename=decorator_function.__module__)
    def new_decorator(*no_args):
        if len(no_args) == 0:
            # called with no args BUT parenthesis: @foo_decorator().
            return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *no_args)

        elif len(no_args) == 1:
            # called with no arg NOR parenthesis: @foo_decorator
            return no_parenthesis_usage(no_args[0], decorator_function, is_impl_first_mode, injected_arg_name)
        else:
            # more than 1 argument: not possible
            raise TypeError("Decorator function '%s' does not accept any argument."
                            "" % decorator_function.__name__)

    return new_decorator


_GENERATED_VARPOS_NAME = 'no_positional_arg'


def create_kwonly_decorator(generated_signature,
                            decorator_function,
                            disambiguator,
                            is_impl_first_mode,      # type: bool
                            is_first_arg_mandatory,  # type: bool
                            injected_arg_name=None   # type: str
                            ):
    """
    Utility method to create a decorator that has only keyword arguments and is implemented by `decorator_function`, in
    implementation-first mode or usage-first mode.

    When the decorator to create has a mandatory argument, it is exposed "as-is" because it is directly protected.

    Otherwise (if all arguments are optional and keyword-only), we modify the created decorator's signature to add a
    leading var-args, so that users will be able to call the decorator without parenthesis.
    When called it checks the length of the var-positional received:
     - 0 positional=called with parenthesis,
     - 1 and the positional argument is not a callable/class : called with parenthesis
     - 1 and the positional argument is a callable/class: if is_first_arg_mandatory we can safely raise a TypeError
     disambiguation is required to know if this is without parenthesis
     (accepted if no mandatory)
     - 2 positional=error).

    Note: we prefer to use this var-arg signature rather than a "(_=None)" signature, because it is more readable for
    the decorator's help.

    :param generated_signature:
    :param decorator_function:
    :param is_impl_first_mode:
    :param is_first_arg_mandatory:
    :param injected_arg_name:
    :return:
    """
    if is_first_arg_mandatory:
        # The first argument is mandatory AND keyword. So we do not need to change the signature to be fully protected
        # indeed python will automatically raise a `TypeError` when users will use this decorator without parenthesis
        # or with positional arguments.
        @with_signature(generated_signature,
                        func_name=decorator_function.__name__,
                        doc=decorator_function.__doc__,
                        modulename=decorator_function.__module__)
        def new_decorator(*no_args, **kwargs):
            # this is a parenthesis call, because otherwise a `TypeError` would already have been raised by python.
            return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *no_args, **kwargs)

        return new_decorator
    else:
        # modify the signature to add a var-positional first
        gen_varpos_param = Parameter(_GENERATED_VARPOS_NAME, kind=Parameter.VAR_POSITIONAL)
        generated_signature = add_signature_parameters(generated_signature, first=[gen_varpos_param])

        # we can fallback to the same case than varpositional
        return create_varpositional_decorator(generated_signature, decorator_function, disambiguator,
                                              is_impl_first_mode=is_impl_first_mode,
                                              is_first_arg_mandatory=is_first_arg_mandatory,
                                              first_arg_name=_GENERATED_VARPOS_NAME,
                                              injected_arg_name=injected_arg_name)


def create_varpositional_decorator(generated_signature,
                                   decorator_function,
                                   disambiguator,
                                   is_impl_first_mode,  # type: bool
                                   is_first_arg_mandatory,  # type: bool
                                   first_arg_name,  # type: str
                                   injected_arg_name=None  # type: str
                                   ):
    """

    :param generated_signature:
    :param decorator_function:
    :param is_impl_first_mode:
    :param is_first_arg_mandatory:
    :param first_arg_name:
    :param injected_arg_name:
    :return:
    """
    @with_signature(generated_signature,
                    func_name=decorator_function.__name__,
                    doc=decorator_function.__doc__,
                    modulename=decorator_function.__module__)
    def new_decorator(*args, **kwargs):
        # Note: since we expose a decorator with a preserved signature and not (*args, **kwargs)
        # we lose the information about the number of arguments *actually* provided.
        # `@with_signature` will send us all arguments, including the defaults (because it has no way to
        # determine what was actually provided by the user and what is just the default). So at this point we may
        # receive several kwargs even if user did not provide them
        #
        # however in this case we are sure that the only positional args that were provided are in *args

        # this is a with-parenthesis call except if the generated varpositional is filled.
        if len(args) in {0, 2}:
            # with parenthesis: @foo_decorator(*args, **kwargs).
            return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *args, **kwargs)

        else:
            # without parenthesis @foo_decorator OR with 1 positional argument such as @foo_decorator(print, **kwargs).
            first_arg_value = args[0]
            if not can_arg_be_a_decorator_target(first_arg_value):
                # we are sure that this was a with-parenthesis call
                return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *args,
                                              **kwargs)
            else:
                # ambiguous case: at this point a no-parenthesis call is still possible.
                return call_in_appropriate_mode(decorator_function, disambiguator,
                                                is_first_arg_mandatory=is_first_arg_mandatory,
                                                name_first_arg_for_msg='*' + first_arg_name,
                                                first_arg_value=first_arg_value,
                                                is_impl_first_mode=is_impl_first_mode,
                                                injected_arg_name=injected_arg_name, args=args, kwargs=kwargs)

    return new_decorator


def create_general_case_decorator(generated_signature,
                                  decorator_function,
                                  disambiguator,
                                  is_impl_first_mode,      # type: bool
                                  is_first_arg_mandatory,  # type: bool
                                  first_arg_name,          # type: str
                                  injected_arg_name=None   # type: str
                                  ):
    """

    :param generated_signature:
    :param decorator_function:
    :param is_impl_first_mode:
    :param is_first_arg_mandatory:
    :param first_arg_name:
    :param injected_arg_name:
    :return:
    """

    @with_signature(generated_signature,
                    func_name=decorator_function.__name__,
                    doc=decorator_function.__doc__,
                    modulename=decorator_function.__module__)
    def new_decorator(*args, **kwargs):
        # Note: since we expose a decorator with a preserved signature and not (*args, **kwargs)
        # we lose the information about the number of arguments *actually* provided.
        # `@with_signature` will send us all arguments, including the defaults (because it has no way to
        # determine what was actually provided by the user and what is just the default). So at this point we may
        # receive several kwargs
        # - even if user did not provide them
        # - and even if user provided them as positional !!

        # >> we have to use signature.bind to get the TRUE first argument
        bound = generated_signature.bind(*args, **kwargs)
        first_arg_value = bound.arguments[first_arg_name]

        if not can_arg_be_a_decorator_target(first_arg_value):
            # we are sure that this was a WITH-parenthesis call
            return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *args, **kwargs)
        elif not is_no_parenthesis_call_possible_from_args_values(generated_signature, bound, first_arg_name):
            # we are sure that this is a WITH-parenthesis call
            return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *args, **kwargs)
        else:
            # ambiguous case: at this point a no-parenthesis call is still possible.
            return call_in_appropriate_mode(decorator_function, disambiguator,
                                            is_first_arg_mandatory=is_first_arg_mandatory,
                                            name_first_arg_for_msg=first_arg_name, first_arg_value=first_arg_value,
                                            is_impl_first_mode=is_impl_first_mode, injected_arg_name=injected_arg_name,
                                            args=args, kwargs=kwargs)

    return new_decorator


# ------------- disambiguation methods -----------
def can_arg_be_a_decorator_target(arg):
    """
    Returns True if the argument received has a type that can be decorated.

    If this method returns False, we are sure that this is a *with*-parenthesis call
    because python does not allow you to decorate anything else than a function or a class

    :param arg:
    :return:
    """
    return callable(arg) or isclass(arg)


def is_no_parenthesis_call_possible_from_args_values(new_ds, bound, name_first_arg):
    """
    Returns False if we are absolutely certain that this is a with-parenthesis call. this can be
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


class AmbiguousFirstArgumentTypeError(TypeError):
    pass


class InvalidMandatoryArgError(TypeError):
    pass


def call_in_appropriate_mode(decorator_function,
                             disambiguator,
                             is_first_arg_mandatory,
                             # first arg
                             name_first_arg_for_msg,
                             first_arg_value,
                             # mode
                             is_impl_first_mode,
                             injected_arg_name,
                             # args
                             args, kwargs
                             ):
    """


    :param decorator_function:
    :param disambiguator:
    :param is_first_arg_mandatory:
    :param name_first_arg_for_msg:
    :param first_arg_value:
    :param is_impl_first_mode:
    :param injected_arg_name:
    :param args:
    :param kwargs:
    :return:
    """
    # call disambiguator (it combines our rules with the ones optionally provided by the user)
    res = disambiguator(first_arg_value)

    if res is FirstArgDisambiguation.is_decorated_target:
        # (1) NO-parenthesis usage: @foo_decorator
        if is_first_arg_mandatory:
            # that's not possible
            raise InvalidMandatoryArgError("function '%s' requires a mandatory argument '%s'. Provided value '%s' does "
                                           "not pass its validation criteria" % (decorator_function.__name__,
                                                                                 name_first_arg_for_msg,
                                                                                 first_arg_value))
        else:
            # ok: do it
            return no_parenthesis_usage(first_arg_value, decorator_function, is_impl_first_mode,
                                        injected_arg_name)

    elif res is FirstArgDisambiguation.is_normal_arg:
        # (2) WITH-parenthesis usage: @foo_decorator(*args, **kwargs).
        return with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name,
                                      *args, **kwargs)

    elif res is FirstArgDisambiguation.is_ambiguous:
        # (3) STILL AMBIGUOUS
        # By default we are very conservative: we do not allow the first argument to be a callable or class if user did
        # not provide a way to disambiguate it
        if is_first_arg_mandatory:
            raise AmbiguousFirstArgumentTypeError(
                "function '%s' requires a mandatory argument '%s'. It cannot be a class nor a callable."
                " If you think that it should, then ask your decorator provider to protect his decorator (see "
                "decopath documentation)" % (decorator_function.__name__, name_first_arg_for_msg))
        else:
            raise AmbiguousFirstArgumentTypeError(
                "Argument '%s' of generated decorator function '%s' is the *first* argument in the signature. "
                "When the decorator is called (1) with only this argument as non-default value and (2) if this "
                "argument is a callable or class, then it is not possible to determine if that call was a "
                "no-parenthesis decorator usage or a with-args decorator usage. If you think that this particular "
                "usage should be allowed, then ask your decorator provider to protect his decorator (see decopath "
                "documentation)" % (name_first_arg_for_msg, decorator_function.__name__))

    else:
        raise ValueError("single-argument disambiguation did not return properly: received %s" % res)


def create_single_arg_callable_or_class_disambiguator(decorator_function,
                                                      is_function_decorator,
                                                      is_class_decorator,
                                                      can_first_arg_be_ambiguous,
                                                      callable_or_cls_firstarg_disambiguator,
                                                      enable_stack_introspection,
                                                      name_first_arg,
                                                      is_first_arg_mandatory,
                                                      ):
    """
    Returns the function that should be used as disambiguator

    :param first_arg_received:
    :return:
    """

    def disambiguate_call(first_arg_received):
        # introspection-based
        if enable_stack_introspection:
            res = disambiguate_using_introspection(decorator_function, name_first_arg, first_arg_received)
            if res is not None:
                return res

        # we want to eliminate as much as possible the args that cannot be first args
        if callable(first_arg_received) and not isclass(first_arg_received) and not is_function_decorator:
            # that function cannot be a decorator target so it has to be the first argument
            return FirstArgDisambiguation.is_normal_arg

        elif isclass(first_arg_received) and not is_class_decorator:
            # that class cannot be a decorator target so it has to be the first argument
            return FirstArgDisambiguation.is_normal_arg

        elif callable_or_cls_firstarg_disambiguator is not None:
            # an explicit disambiguator is provided, use it
            return callable_or_cls_firstarg_disambiguator(first_arg_received)

        else:
            if can_first_arg_be_ambiguous is not None:
                # it has explicitly been set by user
                if can_first_arg_be_ambiguous:
                    # the first arg is declared explicitly as possibly ambiguous.
                    return FirstArgDisambiguation.is_ambiguous
                else:
                    # user set 'can_first_arg_be_ambiguous' to False explicitly: he assumes that this is a decorator
                    return FirstArgDisambiguation.is_decorated_target
            else:
                # default behaviour, depends on mandatory-ness
                if is_first_arg_mandatory:
                    # we can safely do this, it will raise a `TypeError` automatically
                    return FirstArgDisambiguation.is_decorated_target

                else:
                    # The function has only optional parameters > ask for explicit protection to be able to use it
                    # NOTE: now this should NEVER happen because we now force the implementor to take position
                    # return FirstArgDisambiguation.is_ambiguous
                    raise Exception("Internal error - this line of code is not supposed to be hit")

    return disambiguate_call


def disambiguate_using_introspection(decorator_function,  # type: Callable
                                     name_first_arg,      # type: str
                                     first_arg_received   # type: Any
                                     ):
    """
    Tries to disambiguate the call situation betwen with-parenthesis and without-parenthesis using call stack
    introspection.

    Uses inpect.stack() to get the source code where the decorator is being used. If the line starts with a '@' and does
    not contain any '(', this is a no-parenthesis call. Otherwise it is a with-parenthesis call.
    TODO it could be worth investigating how to improve this logic.. but remember that the decorator can also be renamed
      so we can not check a full string expression

    :param decorator_function:
    :param name_first_arg:
    :param first_arg_received:
    :return:
    """
    try:
        # TODO inspect.stack and inspect.currentframe are extremely slow
        # https://gist.github.com/JettJones/c236494013f22723c1822126df944b12
        # --
        # curframe = currentframe()
        # calframe = getouterframes(curframe, 4)
        # --or
        calframe = stack(3)
        # ----
        filename = calframe[5][1]

        # frame = sys._getframe(5)
        # filename = frame.f_code.co_filename
        # frame_info = traceback.extract_stack(f=frame, limit=6)[0]
        # filename =frame_info.filename

        # print(filename)

        if not filename.startswith('<'):
            # normal case
            context_idx = 0 if isclass(first_arg_received) else 1
        else:
            # iPython / jupyter
            # warning('disambiguating input within ipython... special care: this might be incorrect')
            # # TODO strangely the behaviour of stack() is reversed in this case and the deeper the target the more
            #  context we need.... quite difficult to handle in a generic simple way
            raise Exception("Decorator disambiguation using stack introspection is not available in Jupyter/iPython."
                            " Please use the decorator in a non-ambiguous way. For example use explicit parenthesis"
                            " @%s() for no-arg usage, or use 2 non-default arguments, or use explicit keywords. "
                            "Ambiguous argument received: %s, first argument name is '%s'"
                            "" % (decorator_function.__name__, first_arg_received, name_first_arg))

        # --with inspect..
        code_context = calframe[5][4]
        cal_line_str = code_context[context_idx].lstrip()
        # --with
        # cal_line_str = frame_info.line

        # print(cal_line_str)

        if cal_line_str.startswith('@'):
            if '(' not in cal_line_str:
                # crude way
                return FirstArgDisambiguation.is_decorated_target
            else:
                return FirstArgDisambiguation.is_normal_arg
        else:
            # no @, so most probably a with-arg call
            return FirstArgDisambiguation.is_normal_arg

    except Exception:
        return None


# ----------- utility methods to perform the call ---------


def no_parenthesis_usage(decorated, decorator_function, is_impl_first_mode, injected_arg_name):
    """
    called with no arg NOR parenthesis: @foo_decorator
    we have to directly apply the decorator

    :param decorated:
    :param decorator_function:
    :param is_impl_first_mode:
    :param injected_arg_name:
    :return:
    """
    if is_impl_first_mode:
        kw = {injected_arg_name: decorated}
        return decorator_function(**kw)
    else:
        return decorator_function()(decorated)


def with_parenthesis_usage(decorator_function, is_impl_first_mode, injected_arg_name, *args, **kwargs):
    """
    called with no args BUT parenthesis: @foo_decorator().
    we have to return a nested function to apply the decorator

    :param decorator_function:
    :param is_impl_first_mode:
    :param injected_arg_name:
    :param args:
    :param kwargs:
    :return:
    """
    if is_impl_first_mode:
        def decorate(f):
            # use a keyword way so as to handle keyword-only cases
            kwargs[injected_arg_name] = f
            try:
                return decorator_function(*args, **kwargs)
            except TypeError as err:
                # slightly improve the error message when this talks about keyword arguments: we remove the keyword
                # args part because it always contains the full number of optional arguments even if the user did
                # not provide them (that's a consequence of creating a 'true' signature and not *args, **kwargs)
                if type(err) is TypeError and err.args:
                    try:
                        idx = err.args[0].index('takes 0 positional arguments but 1 positional argument (')
                        err.args = (err.args[0][0:(idx+55)] + 'were given.',) + err.args[1:]
                    except:
                        pass
                raise

        return decorate
    else:
        return decorator_function(*args, **kwargs)
