from enum import Enum
from makefun import remove_signature_parameters, with_signature, wraps

try:  # python 3.3+
    from inspect import signature, Parameter
    funcsigs_used = False
except ImportError:
    from funcsigs import signature, Parameter
    funcsigs_used = True


class injected(Enum):
    """Symbols used in your (double) flat-mode signatures to declare where the various objects should be injected"""
    DECORATED = 1
    WRAPPED = 2
    F_ARGS = 3
    F_KWARGS = 4


DECORATED = injected.DECORATED
# A symbol used in flat-mode signatures to declare where the decorated function should be injected


WRAPPED = injected.WRAPPED
# A symbol used in double flat-mode signatures to declare where the wrapped function should be injected


F_ARGS = injected.F_ARGS
# A symbol used in your double flat-mode signatures to declare where the wrapper args should be injected


F_KWARGS = injected.F_KWARGS
# A symbol used in your double flat-mode signatures to declare where the wrapper kwargs should be injected


def make_decorator_spec(impl_function,
                        flat_mode_decorated_name=None  # type: str
                        ):
    """
    Analyzes the implementation function


    If `flat_mode_decorated_name` is set, this is a shortcut for flat mode. In that case the implementation function
    is not analyzed.

    :param impl_function:
    :param flat_mode_decorated_name:
    :return: sig_info, function_for_metadata, nested_impl_function
    """
    # extract the implementation's signature
    implementors_signature = signature(impl_function)

    # determine the mode (nested, flat, double-flat) and check signature
    mode, injected_name, injected_arg, f_args_name, f_kwargs_name = extract_mode_info(implementors_signature,
                                                                                      flat_mode_decorated_name)

    # create the signature of the decorator function to create, according to mode
    if mode is None:
        # *nested: keep the signature 'as is'
        exposed_signature = implementors_signature
        function_for_metadata = impl_function
        nested_impl_function = impl_function

    elif mode is DECORATED:  # flat mode
        # use the same signature, but remove the injected arg.
        exposed_signature = remove_signature_parameters(implementors_signature, injected_name)

        # use the original function for the docstring/module metadata
        function_for_metadata = impl_function

        # generate the corresponding nested decorator
        nested_impl_function = make_nested_impl_for_flat_mode(exposed_signature, impl_function, injected_name)

    elif mode is WRAPPED:
        # *double-flat: the same signature, but we remove the injected args.
        args_to_remove = (injected_name,) + ((f_args_name,) if f_args_name is not None else ()) \
                         + ((f_kwargs_name,) if f_kwargs_name is not None else ())
        exposed_signature = remove_signature_parameters(implementors_signature, *args_to_remove)

        # use the original function for the docstring/module metadata
        function_for_metadata = impl_function

        # generate the corresponding nested decorator
        nested_impl_function = make_nested_impl_for_doubleflat_mode(exposed_signature, impl_function, injected_name,
                                                             f_args_name, f_kwargs_name)

    else:
        raise ValueError("Unknown mode: %s" % mode)

    # create an object to easily access the signature information afterwards
    sig_info = SignatureInfo(exposed_signature)

    return sig_info, function_for_metadata, nested_impl_function


def make_nested_impl_for_flat_mode(decorator_signature, user_provided_applier, injected_name):
    """
    Creates the nested-mode decorator to be used when the implementation is provided in flat mode.

    Note: we set the signature correctly so that this behaves exactly like a nested implementation in terms of
    exceptions raised when the arguments are incorrect. Since the external method is called only once per decorator
    usage and does not impact the decorated object we can afford.

    :param decorator_signature:
    :param user_provided_applier:
    :param injected_name:
    :return:
    """

    @with_signature(decorator_signature)
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
                    except:  # ValueError: substring not found, or anything else actually
                        pass
                raise

        return _apply_decorator

    return _decorator


def make_nested_impl_for_doubleflat_mode(decorator_signature, user_provided_wrapper, injected_name,
                                         f_args_name, f_kwargs_name):
    """
    Creates the nested-mode decorator to be used when the implementation is provided in double-flat mode.

    Note: we set the signature correctly so that this behaves exactly like a nested implementation in terms of
    exceptions raised when the arguments are incorrect. Since the external method is called only once per decorator
    usage and does not impact the decorated object / created wrappe, we can afford.

    :param decorator_signature:
    :param user_provided_wrapper:
    :param injected_name:
    :param f_args_name:
    :param f_kwargs_name:
    :return:
    """

    @with_signature(decorator_signature)
    def _decorator(*args, **kwargs):
        """ The decorator. Its signature will be overriden by `generated_signature` """

        def _apply_decorator(f):
            """ This is called when the decorator is applied to an object `f` """

            # the injected function is f. Add it to the other decorator parameters, under name requested by user.
            kwargs[injected_name] = f

            # create a signature-preserving wrapper using `makefun.wraps`
            @wraps(f)
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


def extract_mode_info(impl_sig,                      # type: Signature
                      flat_mode_decorated_name=None  # type: str
                      ):
    """
    Returns the (name, Parameter) for the parameter with default value DECORATED

    :param impl_sig: the implementing function's signature
    :param flat_mode_decorated_name: an optional name of decorated argument. If provided a "flat mode" is automatically
        set
    :return:
    """
    mode = None
    injected = None
    f_args = None
    f_kwargs = None

    if flat_mode_decorated_name is not None:
        # validate that the 'decorated' parameter is a string representing a real parameter of the function
        if not isinstance(flat_mode_decorated_name, str):
            raise TypeError("'decorated' argument should be a string with the argument name where the wrapped object "
                            "should be injected")

        mode = DECORATED
        try:
            injected = impl_sig.parameters[flat_mode_decorated_name]
        except KeyError:
            return ValueError("Function '%s' does not have an argument named '%s'" % (impl_sig.__name__,
                                                                                      flat_mode_decorated_name))

    else:
        # analyze signature to detect
        for p_name, p in impl_sig.parameters.items():
            if p.default is DECORATED:
                if mode is not None:
                    raise ValueError("only one of `DECORATED` or `WRAPPED` can be used in your signature")
                else:
                    mode = DECORATED
                    injected = p
            elif p.default is WRAPPED:
                if mode is not None:
                    raise ValueError("only one of `DECORATED` or `WRAPPED` can be used in your signature")
                else:
                    mode = WRAPPED
                    injected = p
            elif p.default is F_ARGS:
                f_args = p
            elif p.default is F_KWARGS:
                f_kwargs = p

        if mode in {None, DECORATED} and (f_args is not None or f_kwargs is not None):
            raise ValueError("`F_ARGS` or `F_KWARGS` should only be used if you use `WRAPPED`")

    return mode, (injected.name if injected is not None else None), injected, \
           (f_args.name if f_args is not None else None), (f_kwargs.name if f_kwargs is not None else None)


# -----------


class SignatureInfo(object):
    """
    Represents the knowledge we have on the decorator signature.
    Provides handy properties to separate the code requirements from the implementation (and possibly cache).
    """
    __slots__ = 'exposed_signature', 'first_arg_def', '_use_signature_trick'

    def __init__(self, decorator_signature):
        self.exposed_signature = decorator_signature
        _, self.first_arg_def = get_first_parameter(decorator_signature)
        self._use_signature_trick = False

    @property
    def use_signature_trick(self):
        return self._use_signature_trick

    @use_signature_trick.setter
    def use_signature_trick(self, use_signature_trick):
        # note: as of today python 2.7 backport does not handle it properly, but hopefully it will :)
        # see https://github.com/testing-cabal/funcsigs/issues/33.
        self._use_signature_trick = use_signature_trick and not funcsigs_used

    @property
    def first_arg_name(self):
        return self.first_arg_def.name  # if self.first_arg_def is not None else None

    @property
    def first_arg_name_with_possible_star(self):
        return ('*' if self.is_first_arg_varpositional else '') + self.first_arg_name

    @property
    def first_arg_kind(self):
        return self.first_arg_def.kind  # if self.first_arg_def is not None else None

    @property
    def is_first_arg_keyword_only(self):
        return self.first_arg_kind in {Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD}

    @property
    def is_first_arg_varpositional(self):
        return self.first_arg_kind is Parameter.VAR_POSITIONAL

    @property
    def is_first_arg_positional_only(self):
        return self.first_arg_kind is Parameter.POSITIONAL_ONLY

    @property
    def is_first_arg_mandatory(self):
        return self.first_arg_def.default is Parameter.empty and not self.is_first_arg_varpositional


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
