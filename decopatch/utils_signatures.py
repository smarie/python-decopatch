try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


class DECORATED:
    """A symbol used in your flat-mode signatures to declare where the decorated object should be injected"""
    pass


class WRAPPED:
    """A symbol used in your double flat-mode signatures to declare where the decorated object should be injected"""
    pass


class F_ARGS:
    """A symbol used in your double flat-mode signatures to declare where the wrapper args should be injected"""
    pass


class F_KWARGS:
    """A symbol used in your double flat-mode signatures to declare where the wrapper kwargs should be injected"""
    pass


def extract_mode_info(ds,  # type: Signature
                      decorated=None  # type: str
                      ):
    """
    Returns the (name, Parameter) for the parameter with default value DECORATED

    :param ds:
    :param decorated: an optional name of decorated argument
    :return:
    """
    mode = None
    injected = None
    f_args = None
    f_kwargs = None

    if decorated is not None:
        # validate that the 'decorated' parameter is a string representing a real parameter of the function
        if not isinstance(decorated, str):
            raise TypeError("'decorated' argument should be a string with the argument name where the wrapped object "
                            "should be injected")

        mode = DECORATED
        try:
            injected = ds.parameters[decorated]
        except KeyError:
            return ValueError("Function '%s' does not have an argument named '%s'" % (ds.__name__, decorated))

    else:
        # analyze signature to detect
        for p_name, p in ds.parameters.items():
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


class SignatureInfo(object):
    """
    Represents the knowledge we have on the decorator signature.
    Provides handy properties to separate the code requirements from the implementation (and possibly cache).
    """
    __slots__ = 'exposed_signature', 'first_arg_def'

    def __init__(self, decorator_signature):
        self.exposed_signature = decorator_signature
        _, self.first_arg_def = get_first_parameter(decorator_signature)

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
