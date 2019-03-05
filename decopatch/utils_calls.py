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
