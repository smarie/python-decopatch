from enum import Enum
from inspect import isclass, stack

from decopatch.utils_modes import SignatureInfo


class FirstArgDisambiguation(Enum):
    """
    This enum is used for the output of user-provided first argument disambiguators.
    """
    is_normal_arg = 0
    is_decorated_target = 1
    is_ambiguous = 2


_WITH_PARENTHESIS = FirstArgDisambiguation.is_normal_arg
"""Alias for the case where the arg is a normal arg"""

_NO_PARENTHESIS = FirstArgDisambiguation.is_decorated_target
"""Alias for the case where the arg is a decorated target"""


def can_arg_be_a_decorator_target(arg):
    """
    Returns True if the argument received has a type that can be decorated.

    If this method returns False, we are sure that this is a *with*-parenthesis call
    because python does not allow you to decorate anything else than a function or a class

    :param arg:
    :return:
    """
    return callable(arg) or isclass(arg)


class DecoratorUsageInfo(object):
    """
    Represent the knowledge that we have when the decorator is being used.
    Note: arguments binding is computed in a lazy mode (only if needed)
    """
    __slots__ = 'sig_info', '_first_arg_value', '_bound', 'args', 'kwargs'

    def __init__(self,
                 sig_info,  # type: SignatureInfo
                 args, kwargs):
        self.sig_info = sig_info
        self.args = args
        self.kwargs = kwargs
        self._first_arg_value = DecoratorUsageInfo  # this is our way to say 'uninitialized'
        self._bound = None

    @property
    def first_arg_value(self):
        if self._first_arg_value is DecoratorUsageInfo:  # not yet initialized
            self._first_arg_value = self.bound.arguments[self.sig_info.first_arg_name]
        return self._first_arg_value

    @property
    def bound(self):
        if self._bound is None:
            self._bound = self.sig_info.exposed_signature.bind(*self.args, **self.kwargs)
        return self._bound


def disambiguate_call(dk,  # type: DecoratorUsageInfo
                      disambiguator):
    """

    :return:
    """
    # (1) use the number of args to eliminate a few cases
    if dk.sig_info.use_signature_trick:
        # we expose a *args, **kwargs signature so we see exactly what the user has provided.
        nb_pos_received, nb_kw_received = len(dk.args), len(dk.kwargs)
        if nb_kw_received > 0 or nb_pos_received == 0 or nb_pos_received > 1:
            return _WITH_PARENTHESIS
        dk._first_arg_value = dk.args[0]
    else:
        # we expose a "true" signature, the only arguments that remain in *args are the ones that CANNOT become kw
        nb_posonly_received = len(dk.args)
        if dk.sig_info.is_first_arg_varpositional or dk.sig_info.is_first_arg_positional_only:
            if nb_posonly_received == 0:
                # with parenthesis: @foo_decorator(**kwargs)
                return _WITH_PARENTHESIS
            elif nb_posonly_received >= 2:
                # with parenthesis: @foo_decorator(a, b, **kwargs)
                return _WITH_PARENTHESIS
            else:
                # AMBIGUOUS:
                # no parenthesis: @foo_decorator -OR- with 1 positional argument: @foo_decorator(a, **kwargs).
                # reminder: we can not count the kwargs because they always contain all the arguments
                dk._first_arg_value = dk.args[0]

        else:
            # first arg can be keyword. So it will be in kwargs (even if it was provided as positional).
            if nb_posonly_received > 0:
                raise Exception("Internal error - this should not happen, please file an issue on the github page")

    # (2) Now work on the values themselves
    if not can_arg_be_a_decorator_target(dk.first_arg_value):
        # the first argument can NOT be decorated: we are sure that this was a WITH-parenthesis call
        return _WITH_PARENTHESIS
    elif not dk.sig_info.use_signature_trick:
        # we were not able to use the length of kwargs, but at least we can compare them to defaults.
        if dk.first_arg_value is dk.sig_info.first_arg_def.default:
            # the first argument has NOT been set, we are sure that's WITH-parenthesis call
            return _WITH_PARENTHESIS
        else:
            # check if there is another argument that is different from its default value
            # skip first entry
            params = iter(dk.sig_info.exposed_signature.parameters.items())
            next(params)
            for p_name, p_def in params:
                if dk.bound.arguments[p_name] is not p_def.default:
                    return _WITH_PARENTHESIS

    # (3) still-ambiguous case, the first parameter is the single non-default one and is a callable or class
    # at this point a no-parenthesis call is still possible.
    # call disambiguator (it combines our rules with the ones optionally provided by the user)
    return disambiguator(dk.first_arg_value)


def create_single_arg_callable_or_class_disambiguator(impl_function,
                                                      is_function_decorator,
                                                      is_class_decorator,
                                                      custom_disambiguator,
                                                      enable_stack_introspection,
                                                      signature_knowledge,  # type: SignatureInfo
                                                      ):
    """
    Returns the function that should be used as disambiguator in "last resort" (when the first argument is the single
    non-default argument and it is a callable/class).

    :param first_arg_received:
    :return:
    """

    def disambiguate_call(first_arg_received):
        """
        The first argument received is the single non-default argument and it is a callable/class.
        We should try to disambiguate now.

        :param first_arg_received:
        :return:
        """

        # introspection-based
        if enable_stack_introspection:
            res = disambiguate_using_introspection(impl_function, first_arg_received,
                                                   signature_knowledge.use_signature_trick)
            if res is not None:
                return res

        # we want to eliminate as much as possible the args that cannot be first args
        if callable(first_arg_received) and not isclass(first_arg_received) and not is_function_decorator:
            # that function cannot be a decorator target so it has to be the first argument
            return FirstArgDisambiguation.is_normal_arg

        elif isclass(first_arg_received) and not is_class_decorator:
            # that class cannot be a decorator target so it has to be the first argument
            return FirstArgDisambiguation.is_normal_arg

        elif custom_disambiguator is not None:
            # an explicit disambiguator is provided, use it
            return custom_disambiguator(first_arg_received)

        else:
            # Always say "decorated target" because
            # - if 1+ mandatory arg, we can safely do this, it will raise a `TypeError` automatically
            # - if 0 mandatory args, the most probable scenario for receiving a single callable or class argument is
            # still the no-arg. We do not want to penalize users.
            return FirstArgDisambiguation.is_decorated_target

    return disambiguate_call


def disambiguate_using_introspection(decorator_function,  # type: Callable
                                     first_arg_received,   # type: Any
                                     uses_signature_trick,
                                     ):
    """
    Tries to disambiguate the call situation betwen with-parenthesis and without-parenthesis using call stack
    introspection.

    Uses inpect.stack() to get the source code where the decorator is being used. If the line starts with a '@' and does
    not contain any '(', this is a no-parenthesis call. Otherwise it is a with-parenthesis call.
    TODO it could be worth investigating how to improve this logic.. but remember that the decorator can also be renamed
      so we can not check a full string expression

    :param decorator_function:
    :param first_arg_received:
    :param uses_signature_trick: if True we have to look one less level up in the stack
    :return:
    """
    if isclass(first_arg_received):
        # as of today the introspection mechanism provided below does not work reliably on classes.
        return None

    where_to_look = 4 if uses_signature_trick else 5

    try:
        # TODO inspect.stack and inspect.currentframe are extremely slow
        # https://gist.github.com/JettJones/c236494013f22723c1822126df944b12
        # --
        # curframe = currentframe()
        # calframe = getouterframes(curframe, 4)
        # --or
        calframe = stack(context=1)
        # ----
        filename = calframe[where_to_look][1]

        # frame = sys._getframe(where_to_look)
        # filename = frame.f_code.co_filename
        # frame_info = traceback.extract_stack(f=frame, limit=6)[0]
        # filename =frame_info.filename

        # print(filename)

        if filename.startswith('<'):
            # iPython / jupyter
            # warning('disambiguating input within ipython... special care: this might be incorrect')
            # # TODO strangely the behaviour of stack() is reversed in this case and the deeper the target the more
            #  context we need.... quite difficult to handle in a generic simple way
            raise Exception("Decorator disambiguation using stack introspection is not available in Jupyter/iPython."
                            " Please use the decorator in a non-ambiguous way. For example use explicit parenthesis"
                            " @%s() for no-arg usage, or use 2 non-default arguments, or use explicit keywords. "
                            "Ambiguous argument received: %s." % (decorator_function.__name__, first_arg_received))

        # --with inspect..
        code_context = calframe[where_to_look][4]
        cal_line_str = code_context[0].lstrip()
        # --with ?
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
