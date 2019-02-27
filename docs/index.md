# decopatch

*python decorators made easy.*

[![Python versions](https://img.shields.io/pypi/pyversions/decopatch.svg)](https://pypi.python.org/pypi/decopatch/) [![Build Status](https://travis-ci.org/smarie/python-decopatch.svg?branch=master)](https://travis-ci.org/smarie/python-decopatch) [![Tests Status](https://smarie.github.io/python-decopatch/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-decopatch/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-decopatch/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-decopatch)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-decopatch/) [![PyPI](https://img.shields.io/pypi/v/decopatch.svg)](https://pypi.python.org/pypi/decopatch/) [![Downloads](https://pepy.tech/badge/decopatch)](https://pepy.tech/project/decopatch) [![Downloads per week](https://pepy.tech/badge/decopatch/week)](https://pepy.tech/project/decopatch) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-decopatch.svg)](https://github.com/smarie/python-decopatch/stargazers)

Because of a tiny oddity in the python language, writing decorators without help can be a pain. `decopatch` provides a simple way to solve this issue.

## Motivation

### a- Problem

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
        # this is (2) @say_hello()
        # we have to return a decorator function
        def decorate(f):
            def new_f(...):
                ...
            return new_f
        return decorate
```

Unfortunately, the 'trick' to use is different for almost every type of decorator signature (var-args, keyword-only, all-optional, ...). So if you change your mind about your API during development time (this often happens, at least to me :)), you end up having to change this useless piece of code several times!

### b- Solution

`decopatch` provides a simple way to solve this issue. It always uses the best "trick", so that you do not have to care, you just implement one case:

```python
from decopatch import function_decorator

@function_decorator
def say_hello():
    def _decorate_f(f):
        def new_f(...):
            ...
        return new_f
    return _decorate_f
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

In both cases, generated decorators have a proper `help` and `signature`, so users do not see the difference.

### c- Why something new ?

As opposed to the great [`decorator`](https://github.com/micheles/decorator) and [`wrapt`](https://wrapt.readthedocs.io/) libraries, `decopatch` does not try **at the same time** to help you create decorators and function wrappers. In my opinion creating function wrappers is a completely independent topic, you can wish to do it in with a decorator OR without. 

Nevertheless since it is an important use case, I show below how to do it. If you're interested in this topic, see [`makefun`](https://smarie.github.io/python-makefun/), my fork of `decorator`'s core engine supporting additional use cases such as signature modification.
 

## Installing

```bash
> pip install decopatch
```

## Usage

### a- Flat mode

In this mode the decorator is implemented as a function, that should return the replacement for the decorated item. To create a decorator you have to do two things:
 
 - use `@function_decorator`, `@class_decorator` or `@decorator` on your implementation function
 - declare which variable represents the injected decorated item by using the `DECORATED` keyword as its default value. 
 
Note: if you can not or do not want to add the `DECORATED` default value, you can specify the variable name explicitly with `wraps=<argname>`.

#### *1- Simple with mandatory arg*

Let's create a simple `@add_tag` decorator that adds a tag on the decorated function:

```python
from decopatch import function_decorator, DECORATED

@function_decorator
def add_tag(tag, f=DECORATED):
    """
    This decorator adds the 'my_tag' tag on the decorated function,
    with the value provided as argument

    :param tag: the tag value to set
    :param f: represents the decorated item. Automatically injected.
    :return:
    """
    setattr(f, 'my_tag', tag)
    return f
```

You can test that your new `@add_tag` decorator works:

```python
@add_tag('hello')
def foo():
    return

# let's check that the `foo` function has been correctly decorated
assert foo.my_tag == 'hello'
```

And also that using your decorator without argument raises an error as expected:

```python
@add_tag
def foo():
    return
```

yields `TypeError: add_tag() missing 1 required positional argument: 'tag'`.

Finally, note that calling the decorator with a callable as first argument is even correctly handled:

```python
@add_tag(print)
def foo():
    return

assert foo.my_tag == print  # works !
```

#### *2- Same with all-optional args*

Let's modify the above example so that the argument is optional:

```python
@function_decorator
def add_tag(tag='tag!', f=DECORATED):
    setattr(f, 'my_tag', tag)
    return f
```

You can check that everything works as expected:

```python
@add_tag('hello')                 # normal arg
def foo():
    return
assert foo.my_tag == 'hello'

@add_tag(tag='hello')           # normal kwarg
def foo():
    return
assert foo.my_tag == 'hello'

@add_tag                      # no parenthesis
def foo():
    return
assert foo.my_tag == 'tag!'

@add_tag()                 # empty parenthesis
def foo():
    return
assert foo.my_tag == 'tag!'

@add_tag(print)        # callable as first arg
def foo():
    return
assert foo.my_tag == print

@add_tag(tag=print)  # callable as first kwarg
def foo():
    return
assert foo.my_tag == print
```


#### *3- Function wrapper creator*

In real-world applications you often wish to not only modify the decorated item, but to **replace** it with something else. 

A typical use case is the creation of a **function wrapper**, for example to add behaviours to a function when decorating it. The great `wrapt` and `decorator` libraries have been designed mostly to cover this purpose, but they blend it quite tightly to the decorator creation. Below we show that the same result can be obtained by combining two distinct libraries: `decopatch` to create the decorator, and the library of your choice for the signature-preserving wrapper. In this example we use `makefun`.
 
Let's create a `@say_hello` decorator, that prints a message to stdout before each call to the decorated function. 

```python
from decopatch import function_decorator, DECORATED
from makefun import with_signature

@function_decorator
def say_hello(person="world", f=DECORATED):
    """
    This decorator modifies the decorated function so that a nice hello 
    message is printed before the call.

    :param person: the person name in the print message. Default = "world"
    :param f: represents the decorated item. Automatically injected.
    :return: a modified version of `f` that will print a msg before executing
    """
    # create a wrapper of f that will do the print before call
    # we rely on `makefun.with_signature` to preserve signature
    @with_signature(f)
    def new_f(*args, **kwargs):
        nonlocal person
        print("hello, %s !" % person)  # say hello
        return f(*args, **kwargs)      # call f

    # return the new function
    return new_f
```

Once again, you can check that all call modes are properly implemented:

```python
@say_hello
def foo():
    print("<executing foo>")
foo()

@say_hello()
def bar():
    print("<executing bar>")
bar()

@say_hello("you")
def custom():
    print("<executing custom>")
custom()
```

yields

```bash
hello, world !
<executing foo>
hello, world !
<executing bar>
hello, you !
<executing custom>
```

!!! note "nonlocal in python 2"
    In python 2 the `nonlocal` keyword from [PEP3104](https://www.python.org/dev/peps/pep-3104/) is not available. See [this workaround](https://stackoverflow.com/a/16032631/7262247)

#### *4- Class decorator*

You can similarly use `@class_decorator` to create a decorator that works for classes.



#### *5- Class+Function decorator*

Both `@function_decorator` and `@class_decorator` are actually user-friendly presets for the more generic `@decorator`. If you wish to write a decorator that can be used both for functions and classes, you can use it.


### b- Nested mode

In *nested* mode you write your decorator's signature thinking about what the **user** will have to enter. So for example if you wish to create `@say_hello(person)` you will define `def say_hello(person)`. In that case your function has to return a function. 

In other words, *nested* mode is equivalent to how you write python decorators with arguments today, except that you do not have to write anything special to handle the case where your decorator is used without parenthesis. It is silently redirected to the case where it is used with parenthesis. 

To write decorators in this mode, you only have to decorate them with `@function_decorator`, `@class_decorator` or `@decorator`.

#### *1- Simple with mandatory arg*

We can reproduce the same example than above, in this alternate style:

```python
@function_decorator
def add_tag(tag):
    """
    This decorator adds the 'my_tag' tag on the decorated function,
    with the value provided as argument

    :param tag: the tag value to set
    :param f: represents the decorated item. Automatically injected.
    :return:
    """
    def replace_f(f):
        setattr(f, 'my_tag', tag)
        return f
    return replace_f
```

You can test that your new `@add_tag` decorator works:

```python
@add_tag('hello')
def foo():
    return

# let's check that the `foo` function has been correctly decorated
assert foo.my_tag == 'hello'
```

### c- Behind the scenes

When you use `@function_decorator` or the like, your function is dynamically replaced with another one with the same signature (if you're in *nested* mode) or where the `f` parameter is removed (if you're in *flat* mode). You can see it by using `help` on your function, or by looking at its signature:

```python
help(say_hello)

from inspect import signature
print("Signature: %s" % signature(say_hello))
```

yields

```bash
Help on function say_hello in module my_module:

say_hello(person='world')
    This decorator modifies the decorated function so that a nice hello
    message is printed before the call.
    
    :param person: the person name in the print message. Default = "world"
    :return:

Signature: (person='world')
```


## See Also

 - [decorator](https://github.com/micheles/decorator), the reference library for creating decorators in python. I used it a lot before writing `makefun` and `decopatch`, big thanks to [`micheles`](https://github.com/micheles) !
 - [tutorial 1](https://realpython.com/primer-on-python-decorators/)
 - [tutorial 2](https://www.thecodeship.com/patterns/guide-to-python-function-decorators/)
 - [decorator recipes](https://wiki.python.org/moin/PythonDecoratorLibrary)

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-decopatch](https://github.com/smarie/python-decopatch)
