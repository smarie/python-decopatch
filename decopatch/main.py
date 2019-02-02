from inspect import isclass

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


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


def decorator(*target_filters):
    """
    A decorator to create any kind of decorators, supporting multiple targets.

    To support one type of target, simply provide a `target_filters` that returns True when that kind of object is
    given. For example to only allow functions to be decorated, use `@decorator(callable)`.

    Your decorator implementation function should return as many item replacer functions as there are filters.
    For example if you wish your decorator to support functions and classes:

    ```python
    from inspect import isclass

    @decorator(callable, isclass)
    def my_f_and_c_decorator():

        def f_replacer(f)
            # replace f
            return f_replacement

        def c_replacer(c)
            # replace c
            return c_replacement

        # return the two replacers in the same order than the arguments of @decorator
        return f_replacer, c_replacer
    ```

    :param target_filters:
    :return:
    """
    def decorator_function_replacer(decorator_function):

        # first check if the decorator function has at least one mandatory argument
        ds = signature(decorator_function)
        at_least_one_mandatory_arg = False
        for p_name, p_def in ds.parameters.items():
            if p_def.default is ds.empty and not p_def.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
                at_least_one_mandatory_arg = True
                break

        def new_decorator_function(*args, **kwargs):

            # Detect if the decorator was used without argument
            if not at_least_one_mandatory_arg and len(args) == 1 and len(kwargs) == 0:
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

        return new_decorator_function

    return decorator_function_replacer


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
