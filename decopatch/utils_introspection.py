from enum import Enum
from inspect import isclass, stack

from decopatch.utils_calls import no_parenthesis_usage, with_parenthesis_usage


class FirstArgDisambiguation(Enum):
    """
    This enum is used for the output of user-provided first argument disambiguators.
    """
    is_normal_arg = 0
    is_decorated_target = 1
    is_ambiguous = 2


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
    if isclass(first_arg_received):
        # as of today the introspection mechanism provided below does not work reliably on classes.
        return None

    try:
        # TODO inspect.stack and inspect.currentframe are extremely slow
        # https://gist.github.com/JettJones/c236494013f22723c1822126df944b12
        # --
        # curframe = currentframe()
        # calframe = getouterframes(curframe, 4)
        # --or
        calframe = stack(context=1)
        # ----
        filename = calframe[5][1]

        # frame = sys._getframe(5)
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
                            "Ambiguous argument received: %s, first argument name is '%s'"
                            "" % (decorator_function.__name__, first_arg_received, name_first_arg))

        # --with inspect..
        code_context = calframe[5][4]
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
