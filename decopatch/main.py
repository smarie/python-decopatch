from makefun import with_signature, remove_signature_parameters, add_signature_parameters
from decopatch.utils_signatures import extract_mode_info, DECORATED, WRAPPED, SignatureInfo
from decopatch.utils_disambiguation import create_single_arg_callable_or_class_disambiguator, disambiguate_call, \
    DecoratorUsageInfo
from decopatch.utils_calls import with_parenthesis_usage, no_parenthesis_usage, call_in_appropriate_mode

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter

try:  # python 3.5+
    from typing import Callable, Any, Optional
except ImportError:
    pass


def function_decorator(enable_stack_introspection=False,             # type: bool
                       can_first_arg_be_ambiguous=False,             # type: Optional[bool]
                       callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                       decorated=None,                               # type: Optional[str]
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


def class_decorator(enable_stack_introspection=False,             # type: bool
                    can_first_arg_be_ambiguous=False,             # type: Optional[bool]
                    callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                    decorated=None,                               # type: Optional[str]
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
              enable_stack_introspection=False,             # type: bool
              can_first_arg_be_ambiguous=False,             # type: Optional[bool]
              callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
              decorated=None,                                   # type: str
              ):
    """
    A decorator to create decorators.

    It support two main modes: "nested", and "flat".

    In "flat" mode your implementation is flat:

    ```python
    def my_decorator(a, b, f=DECORATED):
        # ...
        return <replacement for f>
    ```

    For this mode to be automatically detected, your implementation has to have an argument with default value
    `DECORATED`, or a non-None `decorated` argument name should be provided. This argument will be injected with the
    decorated target when your decorator is used.

    In any other case the "nested" mode is activated. In this mode your implementation is nested:

    ```python
    def my_decorator(a, b):
        def replace_f(f):
            # ...
            return <replacement for f>
        return replace_f
    ```

    In both modes, because python language does not redirect no-parenthesis usages (@my_decorator) to no-args usages
    (@my_decorator()), `decopatch` tries to disambiguate automatically the type of call.

    Here is the logic is follows:

     - if your implementation has no arguments at all, a special decorator with variable-length args
    is created and the mode is detected from the number of arguments (0=with empty parenthesis, 1=no parenthesis,
    2+=error)
     - if your implementation has only keyword-only arguments
       - if it has at least a mandatory one, it is exposed "as is" as it is natively protected.
       - otherwise (all arguments are optional), we modify the created decorator's signature to add a
         leading var-args, so that users will be able to call the decorator without parenthesis. The call mode is then
         detected from the number and type of arguments in this var-args (0: with empty parenthesis, 1: disambiguation
         is needed, 2+: error)
     - If you implementation's first argument is a variable-length arg, we can safely say that when it contains 0 or 2+
       elements it is a with-parenthesis call. Otherwise disambiguation is needed
     - in the general case disambiguation works as follows:
       - the first argument is not a callable nor a class, this is a parenthesis call.
       - if the first argument is equal to its default value, this is a parenthesis call
       - if at least two arguments have values different from their default values, this is a parenthesis call
       - otherwise, we enter a "configurable disambiguation zone".


    Finally you can use this function to directly create a "function wrapper" decorator. For this, use
    the `WRAPPED` default value instead of `DECORATED`, and include two arguments with default values `F_ARGS` and
    `F_KWARGS`:

    ```python
    @function_decorator
    def say_hello(person="world", f=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
        '''
        This decorator wraps the decorated function so that a nice hello
        message is printed before each call.

        :param person: the person name in the print message. Default = "world"
        '''
        print("hello, %s !" % person)  # say hello
        return f(*f_args, **f_kwargs)  # call f
    ```

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
    """
    Exception raised when you define a decorator that has no mandatory argument, and for which
    - Introspection is disabled (enable_stack_introspection is False)
    - You do not state clearly if first argument can be ambiguous (can_first_arg_be_ambiguous is None)
    - A custom disambiguator is not provided (callable_or_cls_firstarg_disambiguator is None)
    """
    pass


def create_decorator(impl_function,
                     is_function_decorator=True,  # type: bool
                     is_class_decorator=True,  # type: bool
                     enable_stack_introspection=False,  # type: bool
                     can_first_arg_be_ambiguous=False,  # type: Optional[bool]
                     callable_or_cls_firstarg_disambiguator=None,  # type: Callable[[Any], FirstArgDisambiguation]
                     decorated=None,  # type: Optional[str]
                     ):
    """
    Main function to create a decorator implemented with the `decorator_function` implementation.

    :param impl_function:
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
    implementors_signature = signature(impl_function)

    # determine the mode (nested, flat, double-flat) and check signature
    mode, injected_name, injected_arg, f_args_name, f_kwargs_name = extract_mode_info(implementors_signature, decorated)

    # create the signature of the decorator function to create, according to mode
    if mode is None:
        # *nested: keep the signature 'as is'
        decorator_signature = implementors_signature
        function_for_decorator_metadata = impl_function

    elif mode is DECORATED:  # flat mode
        # use the same signature, but remove the injected arg.
        decorator_signature = remove_signature_parameters(implementors_signature, injected_name)

        # use the original function for the docstring/module metadata
        function_for_decorator_metadata = impl_function

        # generate the corresponding nested decorator
        impl_function = make_nested_impl_for_flat_mode(impl_function, injected_name)

    elif mode is WRAPPED:
        # *double-flat: the same signature, but we remove the injected args.
        args_to_remove = (injected_name, ) + ((f_args_name, ) if f_args_name is not None else ()) \
                         + ((f_kwargs_name, ) if f_kwargs_name is not None else ())
        decorator_signature = remove_signature_parameters(implementors_signature, *args_to_remove)

        # use the original function for the docstring/module metadata
        function_for_decorator_metadata = impl_function

        # generate the corresponding nested decorator
        impl_function = make_nested_impl_for_doubleflat_mode(impl_function, injected_name,
                                                             f_args_name, f_kwargs_name)

    else:
        raise ValueError("Unknown mode: %s" % mode)

    # (2) --- Generate according to the situation--------
    # check if the resulting function has any parameter at all
    if len(decorator_signature.parameters) == 0:
        # (A) no argument at all. Special handling.
        return create_no_args_decorator(impl_function, decorator_function_for_sig=function_for_decorator_metadata)

    else:
        # (B) general case: at least one argument - we have to use the signature information
        sig_info = SignatureInfo(decorator_signature)

        # is our decorator protected ?
        explicitly_protected = enable_stack_introspection \
                               or can_first_arg_be_ambiguous is not None \
                               or callable_or_cls_firstarg_disambiguator is not None  # or is_first_arg_keyword_only

        if not sig_info.is_first_arg_mandatory and not explicitly_protected:
            # if the decorator has all-optional arguments, we prevent it to be created if it is not protected.
            # This is because ambiguous cases ARE nominal cases, they happen all the time
            raise AmbiguousDecoratorDefinitionError("This decorator is ambiguous because it has only optional "
                                                    "arguments. Please provide an explicit protection.")
        else:
            # if the decorator has at least 1 mandatory argument, we allow it to be created but its default behaviour
            # is to raise errors only on ambiguous cases. Usually ambiguous cases are rare (not nominal cases)
            disambiguator = create_single_arg_callable_or_class_disambiguator(impl_function,
                                                                              is_function_decorator,
                                                                              is_class_decorator,
                                                                              can_first_arg_be_ambiguous,
                                                                              callable_or_cls_firstarg_disambiguator,
                                                                              enable_stack_introspection,
                                                                              signature_knowledge=sig_info)

        if sig_info.is_first_arg_keyword_only:
            # in this case the decorator *can* be used without arguments but *cannot* with one positional argument,
            # which will happen in the no-parenthesis case. We have to modify the signature to allow no-parenthesis
            return create_kwonly_decorator(sig_info, impl_function, disambiguator,
                                           function_for_metadata=function_for_decorator_metadata)
        else:
            # general case
            return create_general_case_decorator(sig_info, impl_function, disambiguator,
                                                 function_for_metadata=function_for_decorator_metadata)


def make_nested_impl_for_flat_mode(user_provided_applier, injected_name):
    """
    Creates the nested-mode decorator to be used when the implementation is provided in flat mode.

    :param user_provided_applier:
    :param injected_name:
    :return:
    """

    def _decorator(*args, **kwargs):
        """ The decorator. Its signature will be overriden by `generated_signature` """

        def _apply_decorator(f):
            """ This is called when the decorator is applied to an object `f` """

            # the injected function is f. Add it to the other decorator parameters, under name requested by user.
            kwargs[injected_name] = f
            try:
                return user_provided_applier(*args, **kwargs)
            except TypeError as err:
                # slightly improve the error message when this talks about keyword arguments: we remove the keyword
                # args part because it always contains the full number of optional arguments even if the user did
                # not provide them (that's a consequence of creating a 'true' signature and not *args, **kwargs)
                if type(err) is TypeError and err.args:
                    try:
                        idx = err.args[0].index('takes 0 positional arguments but 1 positional argument (')
                        err.args = (err.args[0][0:(idx + 55)] + 'were given.',) + err.args[1:]
                    except:
                        pass
                raise

        return _apply_decorator
    return _decorator


def make_nested_impl_for_doubleflat_mode(user_provided_wrapper, injected_name, f_args_name, f_kwargs_name):
    """
    Creates the nested-mode decorator to be used when the implementation is provided in double-flat mode.

    :param user_provided_wrapper:
    :param injected_name:
    :param f_args_name:
    :param f_kwargs_name:
    :return:
    """
    def _decorator(*args, **kwargs):
        """ The decorator. Its signature will be overriden by `generated_signature` """

        def _apply_decorator(f):
            """ This is called when the decorator is applied to an object `f` """

            # the injected function is f. Add it to the other decorator parameters, under name requested by user.
            kwargs[injected_name] = f

            # create a signature-preserving wrapper using `makefun.with_signature`
            @with_signature(f)
            def wrapper(*f_args, **f_kwargs):
                # if the user wishes us to inject the actual args and kwargs, let's inject them
                if f_args_name is not None:
                    kwargs[f_args_name] = f_args
                if f_kwargs_name is not None:
                    kwargs[f_kwargs_name] = f_kwargs

                # finally call the user-provided implementation
                return user_provided_wrapper(*args, **kwargs)

            return wrapper
        return _apply_decorator
    return _decorator


def create_no_args_decorator(decorator_function,
                             decorator_function_for_sig=None,
                             ):
    """
    Utility method to create a decorator that has no arguments at all and is implemented by `decorator_function`, in
    implementation-first mode or usage-first mode.

    The created decorator is a function with var-args. When called it checks the length
    (0=called with parenthesis, 1=called without, 2=error).

    Note: we prefer to use this var-arg signature rather than a "(_=None)" signature, because it is more readable for
    the decorator's help.

    :param decorator_function:
    :param decorator_function_for_sig: an alternate function to use for the documentation and module metadata of the
        generated function
    :return:
    """
    if decorator_function_for_sig is None:
        decorator_function_for_sig = decorator_function

    @with_signature(None,
                    func_name=decorator_function_for_sig.__name__,
                    doc=decorator_function_for_sig.__doc__,
                    modulename=decorator_function_for_sig.__module__)
    def new_decorator(*no_args):
        if len(no_args) == 0:
            # called with no args BUT parenthesis: @foo_decorator().
            return with_parenthesis_usage(decorator_function, *no_args)

        elif len(no_args) == 1:
            # called with no arg NOR parenthesis: @foo_decorator
            return no_parenthesis_usage(decorator_function, no_args[0])
        else:
            # more than 1 argument: not possible
            raise TypeError("Decorator function '%s' does not accept any argument."
                            "" % decorator_function.__name__)

    return new_decorator


_GENERATED_VARPOS_NAME = 'no_positional_arg'


def create_kwonly_decorator(sig_info,  # type: SignatureInfo
                            decorator_function,
                            disambiguator,
                            function_for_metadata,
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
     - 1 and the positional argument is a callable/class: disambiguation is required to know if this is without
     parenthesis or with positional arg
     - 2 positional=error).

    Note: we prefer to use this var-arg signature rather than a "(_=None)" signature, because it is more readable for
    the decorator's help.

    :param sig_info:
    :param decorator_function:
    :param function_for_metadata: an alternate function to use for the documentation and module metadata of the
        generated function
    :return:
    """
    if sig_info.is_first_arg_mandatory:
        # The first argument is mandatory AND keyword. So we do not need to change the signature to be fully protected
        # indeed python will automatically raise a `TypeError` when users will use this decorator without parenthesis
        # or with positional arguments.
        @with_signature(sig_info.exposed_signature,
                        func_name=function_for_metadata.__name__,
                        doc=function_for_metadata.__doc__,
                        modulename=function_for_metadata.__module__)
        def new_decorator(*no_args, **kwargs):
            # this is a parenthesis call, because otherwise a `TypeError` would already have been raised by python.
            return with_parenthesis_usage(decorator_function, *no_args, **kwargs)

        return new_decorator
    else:
        # modify the signature to add a var-positional first
        gen_varpos_param = Parameter(_GENERATED_VARPOS_NAME, kind=Parameter.VAR_POSITIONAL)
        sig_info.exposed_signature = add_signature_parameters(sig_info.exposed_signature, first=[gen_varpos_param])
        sig_info.first_arg_def = gen_varpos_param

        # we can fallback to the same case than varpositional
        return create_general_case_decorator(sig_info, decorator_function, disambiguator,
                                             function_for_metadata=function_for_metadata)


def create_general_case_decorator(sig_info,  # type: SignatureInfo
                                  impl_function,
                                  disambiguator,
                                  function_for_metadata,
                                  ):
    """

    :param sig_info:
    :param impl_function:
    :param disambiguator:
    :param function_for_metadata: an alternate function to use for the documentation and module metadata of the
        generated function
    :return:
    """
    @with_signature(sig_info.exposed_signature,
                    func_name=function_for_metadata.__name__,
                    doc=function_for_metadata.__doc__,
                    modulename=function_for_metadata.__module__)
    def new_decorator(*args, **kwargs):
        # Note: since we expose a decorator with a preserved signature and not (*args, **kwargs)
        # we lose the information about the number of arguments *actually* provided.
        # `@with_signature` will send us all arguments, including the defaults (because it has no way to
        # determine what was actually provided by the user and what is just the default). So at this point we may
        # receive several kwargs
        # - even if user did not provide them
        # - and even if user provided them as positional !! (except for var-positional and fuutre positional-only args)

        # disambiguate
        dk = DecoratorUsageInfo(sig_info, args, kwargs)
        disambiguation_result = disambiguate_call(dk, disambiguator)

        # call
        return call_in_appropriate_mode(impl_function, dk, disambiguation_result)

    return new_decorator
