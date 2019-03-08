# Motivation

This page explains why I felt frustrated by the current tools that we developers have at our disposal to develop decorators in python, and eventually why I ended-up writing `decopatch`.

## Problem

In python, a decorator used without arguments such as 

```python
@say_hello  # (1) no-parenthesis
def foo(a, b):
    pass
```

requires a completely different implementation code than

```python
@say_hello()  # (2) empty-parenthesis
def foo(a, b):
    pass
```

Indeed (1) requires `say_hello` to directly return a replacement for the decorated object (in that case function `foo`), while (2) requires `say_hello` to return a **function** that returns a replacement for the decorated object ! This is one more level of nesting. If you wish to handle both situations in a robust way, **you end-up having to design some ridiculously complex code**, relying on some well-known "tricks" based either on checking the type or existence of first argument provided. For example:

```python
def say_hello(f=None):
    if f is not None:
        # this is (1) @say_hello (without parenthesis)
        # we have to directly return a replacement for f
        def new_f(...):
            ...
        return new_f
    else:
        # this is (2) @say_hello() (empty parenthesis)
        # we have to return a decorator function
        def _decorate(f):
            def new_f(...):
                ...
            return new_f
        return _decorate
```

Unfortunately, the 'trick' to use is different for almost every type of decorator signature (var-args, keyword-only, all-optional, ...). So if you change your mind about your API during development time (this often happens, at least to me :)), you end up having to change this useless piece of code several times!

## Solution

`decopatch` provides a simple way to solve this issue. It always uses the best "trick", so that you do not have to care, you just implement one case:

```python
from decopatch import function_decorator

@function_decorator
def say_hello():
    def _decorate(f):
        def new_f(...):
            ...
        return new_f
    return _decorate
```

To ease things even more, `decopatch` also supports a *flat* mode:

```python
from decopatch import function_decorator, DECORATED

@function_decorator
def say_hello(f=DECORATED):
    def new_f(...):
        ...
    return new_f
```

In both cases, generated decorators have a proper `help` and `signature`, so users do not see the difference, the choice of mode is a matter of development style.

## Why something new ?

As opposed to the great [`decorator`](https://github.com/micheles/decorator) and [`wrapt`](https://wrapt.readthedocs.io/) libraries, `decopatch` does not try **at the same time** to help you create decorators **and** (signature-preserving) function wrappers. In my opinion creating function wrappers is a completely independent topic, you can wish to do it in with a decorator OR without. Nevertheless since it is an important use case, the documentation shows [how to do it](). If you're interested in this topic, see [`makefun`](https://smarie.github.io/python-makefun/), my fork of `decorator`'s core engine supporting additional use cases such as signature modification.
 
Also, note that (at the time of writing so with `decorator` 4.3.2 and `wrapt` 1.11.1):
 
 - none of `wrapt` and `decorator` preserve the exposed decorator's signature: they both rely on an extra optional argument (`func=None` and `wrapped=None` respectively).
 - `decorator` relies on the `__wrapped__` special field to trick the `signature` module about the true signature of the decorator. You can check it by deleting this field on your decorator, and query its signature again: you will see the true signature of your decorator (the one seen by the python interpreter when calling the decorator).
 - none of `decorator` and `wrapt` handle the no-parenthesis case natively. `wrapt` [explains which lines of codes you have to enter](https://wrapt.readthedocs.io/en/latest/decorators.html#decorators-with-optional-arguments) while with `decorator` you have to write the parenthesis.

## Could we solve this directly in the python language instead ?

That would be great ! See my [PEP proposal draft](../pep_proposal).
