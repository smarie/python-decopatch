from inspect import isclass

from makefun import with_signature, remove_signature_parameters, add_signature_parameters

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


class DECORATED:
    """A symbol used in you implementation-first signatures to declare where the decorated object should be injected"""
    pass


def function_decorator(decorator_function):
    """
    A decorator to create function decorators

    :param decorator_function:
    :return:
    """
    return decorator(callable)(decorator_function)


def class_decorator(decorator_function):
    """
    A decorator to create class decorators

    :param decorator_function:
    :return:
    """
    return decorator(isclass)(decorator_function)


def default_first_arg_disambiguator(f):
    """Default implementation of 'first_arg_disambiguator': if it is not a callable or a class, then it can be a first
    arg."""
    return not callable(f) and not isclass(f)


def decorator(*target_filters,
              wraps=None,
              first_arg_disambiguator=None,
              disable_no_arg_detection=False):
    """
    A decorator to create decorators.

    It support two modes: "implementation-first", and "usage-first".


    By default, the f parameter is automatically detected in your signature if you correctly use the DECORATED default
    value. Alternately you can specify the argument name explicitly by using @decorator(wraps=<argname>).

    :param target_filters:
    :return:
    """

    if len(target_filters) == 1 and callable(target_filters[0]):
        # called without argument
        return create_decorator(target_filters[0])
    else:
        # called with argument
        def deco(d):
            return create_decorator(d, *target_filters, wraps=wraps, first_arg_disambiguator=first_arg_disambiguator,
                                    disable_no_arg_detection=disable_no_arg_detection)
        return deco


def create_decorator(decorator_function,
                     *target_filters,
                     wraps=None,
                     first_arg_disambiguator=None,
                     disable_no_arg_detection=False):

    # set default value for is_of_wrapped_type
    if first_arg_disambiguator is None:
        first_arg_disambiguator = default_first_arg_disambiguator

    # extract the signature
    ds = signature(decorator_function)

    # determine the mode
    if wraps is not None:
        # this is an implementation-first declaration
        implementation_first = True

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

        # if there is a parameter with default=DECORATED that's an impl-first mode
        implementation_first = wraps is not None

    # now generate the function according to the mode
    if implementation_first:
        # create the signature of the decorator function to be created
        new_ds = remove_signature_parameters(ds, wraps)

        # can this decorator be called without argument ?
        # can_be_called_without_args = has_no_mandatory_arg(new_ds)

        # get information about the first parameter
        name_first_arg, p = get_first_parameter(new_ds)

        if name_first_arg is None:
            # no argument at all. Special handling
            @with_signature(None, func_name=decorator_function.__name__, doc=decorator_function.__doc__,
                            modulename=decorator_function.__module__)
            def new_decorator(*args):
                if len(args) == 0:
                    # called with no args and parenthesis ()
                    def decorate(f):
                        return decorator_function(f)
                    return decorate
                elif len(args) == 1:
                    # called without arg nor parenthesis
                    return decorator_function()
                else:
                    raise TypeError("Decorator function '%s' does not accept any argument."
                                    "" % decorator_function.__name__)
        else:
            type_hint = get_type_hint(p) if p is not None else None
            first_arg_kind = p.kind if p is not None else None

            @with_signature(new_ds, func_name=decorator_function.__name__, doc=decorator_function.__doc__,
                            modulename=decorator_function.__module__)
            def new_decorator(*args, **kwargs):

                # try to detect if decorator was used without arguments
                # in that case a single argument would be passed to the generated decorator.
                # however since we prefer to expose a decorator with a preserved signature and not (*args, **kwargs)
                # we lose the information about the number of arguments actually provided.
                # we may receive several args and kwargs if there are optional arguments (even if user did not provide them)

                if len(args) + len(kwargs) == 0:
                    # (1) this can only happen if the decorator function has no argument
                    # AND it is called with explicit parenthesis such as `@my_decorator()`
                    # so we are sure that this is a parenthesis call
                    was_used_without_parenthesis = False
                else:
                    # Try to determine if this call is a 'no-arg' call
                    if disable_no_arg_detection:
                        # deactivated : we always assume that we are called with arguments
                        # (implementor has to do the proper checks)
                        was_used_without_parenthesis = False

                    elif first_arg_kind in {Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD}:
                        # (2) the first argument CANNOT be positional, so `@new_decorator` cannot be used without
                        # parenthesis (it would raise an exception).
                        # So we are sure that if we reach this code, that's because a correct call with kw args was made
                        was_used_without_parenthesis = False

                    else:
                        # There is a possibility that the caller sent a single argument (even if we see more here
                        # because the defaults have been added), and that this results from a non-parenthesis use.
                        if len(args) >= 1:
                            # (3) because of the way `@with_signature` works as of today, this can only happen if the
                            # decorator signature has a positional-only (not possible in python today)
                            # or a var positional
                            name_of_first_arg_received = name_first_arg
                            first_arg_received = args[0]
                        else:
                            # (4) normal case, almost all cases fall here (because `@with_signature` redirect all to kw)
                            # TODO unfortunately this does not work in versions of python < 3.6 (=before PEP0468)
                            # So we will have to add an option to `@with_signature` so that we can grab them in order
                            name_of_first_arg_received, first_arg_received = next(iter(kwargs.items()))

                        if name_of_first_arg_received != name_first_arg:
                            # the order of received arguments is different from the one in the signature
                            # so this is a keyword-based call as in @my_decorator(a=1)
                            # we are sure that parenthesis were used
                            was_used_without_parenthesis = False
                        else:
                            # ----- DISAMBIGUATION ------
                            # check the type: bad idea, users can do it if they want to
                            # try:
                            #     is_candidate_wrapped_of_required_type = isinstance(first_arg_received, type_hint)
                            # except TypeError:
                            #     is_candidate_wrapped_of_required_type = None  # we do not know
                            #
                            # if is_candidate_wrapped_of_required_type:
                            #     #
                            #     was_used_without_parenthesis = False

                            if first_arg_disambiguator(first_arg_received):
                                # default = not callable(first_arg_received) and not isclass(first_arg_received)
                                # the disambiguator tells us that this can not be a decorated target
                                was_used_without_parenthesis = False
                            else:
                                # !!!! THIS IS A NO-PARENTHESIS CALL !!!!
                                was_used_without_parenthesis = True

                if was_used_without_parenthesis:
                    kw = {wraps: first_arg_received}
                    return decorator_function(**kw)
                else:
                    def decorate(f):
                        # add the wraped item to the arguments
                        kwargs[wraps] = f
                        return decorator_function(*args, **kwargs)
                    return decorate


    else:

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


def get_type_hint(p  # type: Parameter
                  ):
    if p.annotation is p.empty:
        return None
    else:
        return p.annotation


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
