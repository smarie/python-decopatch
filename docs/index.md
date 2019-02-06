# decopatch

*Create decorators easily in python.*

[![Build Status](https://travis-ci.org/smarie/python-decopatch.svg?branch=master)](https://travis-ci.org/smarie/python-decopatch) [![Tests Status](https://smarie.github.io/python-decopatch/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-decopatch/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-decopatch/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-decopatch) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-decopatch/) [![PyPI](https://img.shields.io/badge/PyPI-decopatch-blue.svg)](https://pypi.python.org/pypi/decopatch/)

(work in progress)

## Motivation

Writing decorators in python without help is a pain, for two main reasons.

**First**, it is difficult for developers because there are two concurrent ways to think when they design their api:

 - if you think **"usage-first"** you will write your decorator's signature thinking about what the user will have to enter. So for example if you wish to create `@say_hello(person)` you will define `def say_hello(person)`.
 
 - if you think **"implementation-first"** you will write your decorator's signature thinking about what you need to actually implement the decorator. So you will define `def say_hello(f, person)`. Unfortunately such a signature can not directly be declared as a decorator in python today.

This situation could be ok if there was not **the other, really annoying problem**. This other problem is that a decorator used without arguments such as 

```python
@say_hello
def foo(a, b):
    pass
```

requires a completely different implementation code (basically a different nesting level) than

```python
@say_hello()
def foo(a, b):
    pass
```

If you wish to handle both situations in a robust way, you end-up with extremely complex code, for something that should not be complex.

`decopatch` provides a simple answer to both issues. Compared to its main source of inspiration, the great [`decorator`](https://github.com/micheles/decorator) library, it brings the following improvements:

 - it does not try to solve the above problems AND the problem of creating signature-preserving wrappers at the same time. To solve the second problem I wrote `makefun`, you can [check it out](https://smarie.github.io/python-makefun/).
 - it tries to provide a more flexible and intuitive API 

## Installing

```bash
> pip install decopatch
```

## Usage

### a- Implementation-first

With `decopatch` you can write decorators in an "implementation-first" way. For this you have to do two things:
 
 - use `@decorator` on your function
 - declare which variable represents the decorated item with the `DECORATED` keyword

#### *Simplest example*

Let's create a simple `@add_tag` decorator that adds a tag on the decorated function:

```python
from decopatch import decorator, DECORATED

@decorator
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

You can test that it works:

```python
@add_tag('hello')
def foo():
    return

# let's check that the `foo` function has been correctly decorated
assert foo.my_tag == 'hello'
```

And also that using your decorator without argument raises a `TypeError` as expected:

```python
@add_tag
def foo():
    return
```

raises `TypeError: add_tag() missing 1 required positional argument: 'tag'`. 

If you are not familiar with python decorators, you might think that this is obvious, but it is actually not: in plain python you have to handle it explicitly in your code. `decopatch` improves development time and code readability by implementing this behaviour automatically.


#### *Typical real-world example: "wrapper" decorators*

In real-world applications you often wish to not only modify the decorated item, but to **replace** it with something else. 

A typical use case is the creation of a **function wrapper**, for example to add behaviours to a function when decorating it. In the example below we create a `@say_hello` decorator, that prints a message to stdout before each call to the decorated function. The wrapper creation itself is made with the help of the `makefun` package, but you could use any other package of your choice (such as `wrapt.wraps` or `decorator.decorate`).

```python
from decopatch import decorator, DECORATED
from makefun import with_signature

@decorator
def say_hello(person="world", f=DECORATED):
    """
    This decorator modifies the decorated function so that a nice hello 
    message is printed before the call.

    :param person: the person name in the print message. Default = "world"
    :param f: represents the decorated item. Automatically injected.
    :return:
    """
    # create a wrapper of f that will do the print before call
    # we rely on `@makefun.with_signature` to preserve signature
    @with_signature(f)
    def say_hello_and_call_f(*args, **kwargs):
        nonlocal person
        print("hello, %s !" % person)  # say hello
        return f(*args, **kwargs)      # call f

    # return the wrapper
    return say_hello_and_call_f
```

Once again, you can check that all call modes are properly implemented:

```python
@say_hello
def foo():
    return

foo()  # prints 'hello, world !'

@say_hello()
def bar():
    return

bar()  # prints 'hello, world !'

@say_hello("you")
def custom():
    return
    
custom()  # prints 'hello, you !'
```

yields

```bash
hello, world !
hello, world !
hello, you !
```

!!! note "nonlocal in python 2"
    In python 2 the `nonlocal` keyword from [PEP3104](https://www.python.org/dev/peps/pep-3104/) is not available. See [this workaround](https://stackoverflow.com/a/16032631/7262247)

#### Behind the scenes

When you use `@decorator`, your function is dynamically replaced with another one, where the `f` parameter is removed. You can see it by using `help` on your function, or by looking at its signature:

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

By default, the `f` parameter is automatically detected in your signature if you correctly use the `DECORATED` default value. Alternately you can specify the argument name explicitly by using `@decorator(wraps=<argname>)`.


### b- Usage-first

TODO

### c- Advanced topics

In very rare cases, you want to create a decorator  

 - that accepts to be called with a single argument (i.e. it has a single mandatory argument, or only optional ones)
 - where the first argument in the signature, except the `DECORATED` one, is a callable or a class. 
 
For example the following dummy decorator will replace the decorated function with its argument:

```python
@decorator
def replace_with(g, f=DECORATED):
    """replace the decorated function with its argument"""
    return g
```

If you try to use it

```python
def foo():
    pass

@replace_with(foo)
def bar():
    pass
```

Surprisingly it fails ! 

```bash
TypeError: replace_with() missing 1 required positional argument: 'g'
```

This is because there is **absolutely no way in the python language** (if you know one, let me know !) to disambiguate the above case from the "no-arg" usage below:

```python
@replace_with
def bar_no_arg():
    pass
```

Hopefully there are many workarounds if you use `decopatch`. The easiest ones consist in changing your decorator's signature:

 - so that the first argument is keyword-only. **This is the most reliable thing to do**. For this, simply add a `*` before your first argument:
 
```python
@decorator
def replace_with(*, g, f=DECORATED):
    # ...
``` 

 - or if the first argument is optional, so that the callable/class is not the first in the list. In this case you have to either declare a type hint or perform manual validation in the code:

```python
@decorator
def replace_with(a: int=None, g=None, f=DECORATED):
    # ...
    
# or

@decorator
def replace_with(a=None, g=None, f=DECORATED):
    if not isinstance(a, int):
        raise TypeError()
    # ...
``` 

 - or if the first argument is mandatory, so that it is not alone (at least two mandatory arguments)

```python
@decorator
def replace_with(g, a, f=DECORATED):
    # ...
``` 

If you can not afford a signature change, there are two other ways to work around this problem:
 
 - change the default detector for first argument disambiguation. By default if a single argument is received, it will be assumed to be the true first arg (and not the decorator's target), if it is not a callable nor a class. If you are sure that a function of a certain type, or a class with certain caracteristics, can only be the argument and not the decorated object, then you can override this default logic. For example we could use `@decorator(first_arg_disambiguator=lambda g: g in {foo})` in the above code.



## See Also

 - [decorator](https://github.com/micheles/decorator), the reference library for creating decorators in python. I used it a lot before writing `makefun` and `decopatch`, big thanks to [`micheles`](https://github.com/micheles) !
 - [tutorial 1](https://realpython.com/primer-on-python-decorators/)
 - [tutorial 2](https://www.thecodeship.com/patterns/guide-to-python-function-decorators/)
 - [decorator recipes](https://wiki.python.org/moin/PythonDecoratorLibrary)

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-decopatch](https://github.com/smarie/python-decopatch)
