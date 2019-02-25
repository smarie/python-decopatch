class DECORATED:
    """A symbol used in you implementation-first signatures to declare where the decorated object should be injected"""
    pass


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


# def get_type_hint(p  # type: Parameter
#                   ):
#     if p.annotation is p.empty:
#         return None
#     else:
#         return p.annotation


# def has_no_mandatory_arg(ds  # type: Signature
#                          ):
#     """
#     Returns
#     :param ds:
#     :return:
#     """
#     at_least_one_mandatory_arg = False
#     for p_name, p_def in ds.parameters.items():
#         if p_def.default is ds.empty and \
#                 not p_def.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
#             at_least_one_mandatory_arg = True
#             break
#
#     return not at_least_one_mandatory_arg
#

# class NonUniqueVarPositionalArgError(Exception):
#     pass
#
#
# def get_unique_varpositional_arg(bound, varposargname):
#     try:
#         first_positional_arg_value = bound.arguments[varposargname]
#     except KeyError:
#         pass
#     else:
#         if len(first_positional_arg_value) == 1:
#             return first_positional_arg_value[0]
#     raise NonUniqueVarPositionalArgError()
