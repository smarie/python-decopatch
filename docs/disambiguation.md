# Disambiguation principles

As stated in the [introduction](../index), without language modification (see [proposal](../pep_proposal)) or additional knowledge or source code introspection, python is just **not capable** of detecting that `@say_hello(foo)` is different from `@say_hello` applied to function `foo` without parenthesis.

However there are well-known "tricks" to perform a disambiguation that covers most standard cases. `decopatch` is basically a collection of such tricks. Some of them are static, based on your decorator's signature, and some others are dynamic, based on the received arguments. This section explains what happens behind the scenes.

The reader is encouraged to get familiar with the basic `decopatch` principles first by reading the  [introduction](../index). In particular the two main development styles (nested and flat) are assumed to be understood. All examples below use the "flat" style, but the equivalent "nested" style would lead to the exact same result.

## 1- no-args decorators

It is probably quite useless to use `decopatch` if your decorator has no arguments, except if you wish to easily support with- and without- parenthesis usage. This is how you can do it 

```python
from decopatch import decorator, DECORATED

@decorator
def replace_with_hello(f=DECORATED):
    """
    Decorator to replace anything with the 'hello' string
    """
    return 'hello'
```

You can of course test that it works fine:

```python
@replace_with_hello  # no parenthesis
def foo():
    pass
assert foo == 'hello'

@replace_with_hello()  # with parenthesis
def foo():
    pass
assert foo == 'hello'
```

In this particular case, `decopatch` does not expose a decorator with no arguments as you would expect, but it instead adds a "dummy" var-positional argument named `_`, so that both with- and without- parenthesis usages are supported: 

```
>>> help(replace_with_hello)
Help on function replace_with_hello in module ...:

replace_with_hello(*_)
    Decorator to replace anything by the 'hello' string.
```

If your users try to input arguments they will get a `TypeError`, except if they provide a single argument that is a callable or a class. In that case we have no means to disambiguate so we prefer to consider that this is a no-parenthesis usage, rather than trying complex disambiguation tricks. After all, your decorator is supposed to have no arguments :)

```python
replace_with_hello(1)      # TypeError: function 'replace_with_hello' does not accept any argument.
replace_with_hello(print)  # no error !
```

See `create_no_args_decorator` in the [source code](https://github.com/smarie/python-decopatch/blob/master/decopatch/main.py) for details.

## 2- keyword-only decorators

### 1+ mandatory argument(s)

If your decorator is keyword-only and has **at least one mandatory argument**:

```python
@decorator
def replace_with(*, replacement, f=DECORATED):
    """ Decorator to replace anything with the <replacement> object. """
    return replacement
```

then everything is very easy for `decopatch`: it can expose your desired signature directly, users have no way to use it in an ambiguous manner, and a successful call will always be a with-parenthesis call. 

```python
@replace_with(replacement='hello')
def foo():
    pass
assert foo == 'hello'

replace_with(1)    # TypeError: replace_with() takes 0 positional arguments
replace_with(str)  # TypeError: replace_with() takes 0 positional arguments
```

See `create_kwonly_decorator` in the [source code](https://github.com/smarie/python-decopatch/blob/master/decopatch/main.py) for details.

### 0 mandatory arguments

If your decorator is keyword-only but has **no mandatory argument**:

```python
@decorator
def replace_with(*, replacement='hello', f=DECORATED):
    """
    Decorator to replace anything with the <replacement> object.
    Default value is 'hello'.
    """
    return replacement
```

`decopatch` automatically adds a dummy var-positional argument named `_` to the decorator signature so that your users can use it without arguments nor parenthesis:

```
>>>help(replace_with)
Help on function replace_with in module ...:
replace_with(*_, replacement='hello')
    Decorator to replace anything with the <replacement> object.
```

Then disambiguations are handled similarly to all other decorators (see below).

See `create_kwonly_decorator` in the [source code](https://github.com/smarie/python-decopatch/blob/master/decopatch/main.py) for details.

## 3- General case

In the general case, disambiguation is made of two phases: first eliminating cases for which we have no doubts, then handling the remaining ambiguous cases.

See `disambiguate_call` in the [source code](https://github.com/smarie/python-decopatch/blob/master/decopatch/utils_disambiguation.py) for details.

**a- Eliminating easy cases:**

 * we look at the number of positional and keyword arguments to eliminate cases that can not be a "no-parenthesis" usage
 * we look at the value of the argument received to eliminate further: for example, if it is not a callable nor a class it is has to be provided with parenthesis.

**b- Handling still-ambiguous cases**

If we reach this part, that's because the first argument in the signature is 

 - a callable or a class,
 - positional (or in python 2, is different from its default value), 
 - and it is the only one (or in python 2, the only one different from its default value)

Note: python 2 behaviour should align when this [`funcsigs` issue](https://github.com/testing-cabal/funcsigs/issues/33) is fixed.

In that scenario, `decopatch` makes the least worst guess: **this is probably a no-parenthesis call**. Because it is not very probable that your decorator is made to receive a function or a class as first argument.

However you can change this default behaviour, by providing additional knowledge.

First, you can **explicitly declare that your decorator is a function-only or class-only decorator**, by using `@decorator(is_function_decorator=False)` or `(is_class_decorator=False)`, or by using the shortcut aliases `@class_decorator` or `@function_decorator` respectively. In that case, `decopatch` will know that for example a class received by a function decorator is probably a with-parenthesis first argument.

You can also **provide an explicit disambiguation function** (`custom_disambiguator=...`). This function will only be called for ambiguous cases. It should accept a single argument (the first argument's value), and should return either `FirstArgDisambiguation.is_normal_arg` or `FirstArgDisambiguation.is_decorated_target`. It can also return `FirstArgDisambiguation.is_ambiguous` if it can not decide ; in which case an exception will be raised. For your convenience, you can use the predefined disambiguators `custom_disambiguator=with_parenthesis` or `custom_disambiguator=no_parenthesis` if an ambiguous first argument should always be handled as an arg (with parenthesis) or as the decorated target (no parenthesis) respectively.

Finally as a last resort scenario you can **enable introspection** (`enable_stack_introspection=True`). This beta feature seems to only work reliably with function decorators, because `inspect.stack` does not provide a reliable way to access the decorator usage source code line when used on a class. Note that it seems to fail when used with `python >=3.8`.
