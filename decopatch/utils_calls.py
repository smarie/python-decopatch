def no_parenthesis_usage(decorator_function, decorated):
    """
    called with no arg NOR parenthesis: @foo_decorator
    we have to directly apply the decorator

    :param decorated:
    :param decorator_function:
    :return:
    """
    return decorator_function()(decorated)


def with_parenthesis_usage(decorator_function, *args, **kwargs):
    """
    called with no args BUT parenthesis: @foo_decorator().
    we have to return a nested function to apply the decorator

    :param decorator_function:
    :param args:
    :param kwargs:
    :return:
    """
    return decorator_function(*args, **kwargs)
