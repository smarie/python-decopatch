#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.


def create_test_varpositional():

    from decopatch import class_decorator, DECORATED

    @class_decorator
    def replace_with(*args, cls=DECORATED):
        # lets make sure that DECORATED has been injected
        assert cls is not DECORATED
        # and replace the class with the tuple of varpos arguments, just for easy check
        return args

    return replace_with
