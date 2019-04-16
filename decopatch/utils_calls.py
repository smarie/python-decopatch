from decopatch.utils_disambiguation import FirstArgDisambiguation


class AmbiguousFirstArgumentTypeError(TypeError):
    pass


class InvalidMandatoryArgError(TypeError):
    pass


def call_in_appropriate_mode(impl_function,
                             dk,  # type: DecoratorUsageInfo
                             disambiguation_result  # type: FirstArgDisambiguation
                             ):
    """


    :param impl_function:
    :param dk:
    :param disambiguation_result:
    :return:
    """
    if disambiguation_result is FirstArgDisambiguation.is_decorated_target:
        # (1) NO-parenthesis usage: @foo_decorator
        if dk.sig_info.is_first_arg_mandatory:
            # that's not possible
            raise InvalidMandatoryArgError("function '%s' requires a mandatory argument '%s'. Provided value '%s' does "
                                           "not pass its validation criteria"
                                           "" % (impl_function.__name__, dk.sig_info.first_arg_name_with_possible_star,
                                                 dk.first_arg_value))
        else:
            # ok: do it
            return no_parenthesis_usage(impl_function, dk.first_arg_value)

    elif disambiguation_result is FirstArgDisambiguation.is_normal_arg:
        # (2) WITH-parenthesis usage: @foo_decorator(*args, **kwargs).
        return with_parenthesis_usage(impl_function, dk=dk)

    elif disambiguation_result is FirstArgDisambiguation.is_ambiguous:
        # (3) STILL AMBIGUOUS
        # By default we are very conservative: we do not allow the first argument to be a callable or class if user did
        # not provide a way to disambiguate it
        if dk.sig_info.is_first_arg_mandatory:
            raise AmbiguousFirstArgumentTypeError(
                "function '%s' requires a mandatory argument '%s'. It cannot be a class nor a callable."
                " If you think that it should, then ask your decorator provider to protect his decorator (see "
                "decopath documentation)" % (impl_function.__name__, dk.sig_info.first_arg_name_with_possible_star))
        else:
            raise AmbiguousFirstArgumentTypeError(
                "Argument '%s' of generated decorator function '%s' is the *first* argument in the signature. "
                "When the decorator is called (1) with only this argument as non-default value and (2) if this "
                "argument is a callable or class, then it is not possible to determine if that call was a "
                "no-parenthesis decorator usage or a with-args decorator usage. If you think that this particular "
                "usage should be allowed, then ask your decorator provider to protect his decorator (see decopath "
                "documentation)" % (dk.sig_info.first_arg_name_with_possible_star, impl_function.__name__))

    else:
        raise ValueError("single-argument disambiguation did not return properly: received %s" % disambiguation_result)


def no_parenthesis_usage(decorator_function, decorated):
    """
    called with no arg NOR parenthesis: @foo_decorator
    we have to directly apply the decorator

    :param decorated:
    :param decorator_function:
    :return:
    """
    return decorator_function()(decorated)


def with_parenthesis_usage(decorator_function, dk=None, args=None, kwargs=None):
    """
    called with no args BUT parenthesis: @foo_decorator().
    we have to return a nested function to apply the decorator

    Note: this method can be either called with a non-none args and kwargs, OR with a non-none dk (a DecoratorUsageInfo)

    :param decorator_function:
    :param dk: all the call context in a DecoratorUsageInfo object. When this is provided, args and kwargs should be
        None
    :param args:
    :param kwargs:
    :return:
    """
    if dk is not None and not dk.sig_info.use_signature_trick:
        # the signature trick is not exposed, so all arguments are redirected to named arguments
        # we therefore cannot yet call decorator_function(*args, **kwargs)
        # See https://github.com/smarie/python-makefun/issues/34: when it is fixed use the fix
        if args is not None or kwargs is not None:
            raise ValueError("internal error - please report")
        args = dk.args
        kwargs = dk.kwargs

        new_args = tuple(kwargs.pop(k) for k in dk.sig_info.argnames_before_varpos_arg) + args
        return decorator_function(*new_args, **kwargs)

    else:
        if dk is None:
            args = args if args is not None else ()
            kwargs = kwargs if kwargs is not None else dict()
        else:
            args = dk.args
            kwargs = dk.kwargs
        return decorator_function(*args, **kwargs)
