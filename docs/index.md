# decopatch

*python decorators made easy.*

[![Python versions](https://img.shields.io/pypi/pyversions/decopatch.svg)](https://pypi.python.org/pypi/decopatch/) [![Build Status](https://github.com/smarie/python-decopatch/actions/workflows/base.yml/badge.svg)](https://github.com/smarie/python-decopatch/actions/workflows/base.yml) [![Tests Status](./reports/junit/junit-badge.svg?dummy=8484744)](./reports/junit/report.html) [![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744)](./reports/coverage/index.html) [![codecov](https://codecov.io/gh/smarie/python-decopatch/branch/main/graph/badge.svg)](https://codecov.io/gh/smarie/python-decopatch) [![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744)](./reports/flake8/index.html)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-decopatch/) [![PyPI](https://img.shields.io/pypi/v/decopatch.svg)](https://pypi.python.org/pypi/decopatch/) [![Downloads](https://pepy.tech/badge/decopatch)](https://pepy.tech/project/decopatch) [![Downloads per week](https://pepy.tech/badge/decopatch/week)](https://pepy.tech/project/decopatch) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-decopatch.svg)](https://github.com/smarie/python-decopatch/stargazers)

Because of a tiny oddity in the python language, writing decorators without help can be a pain because you have to handle the no-parenthesis usage [explicitly](./motivation). `decopatch` provides a simple way to solve this issue so that writing decorators is simple and straightforward.

## Installing

```bash
> pip install decopatch
```

## Usage

### 1- As usual, a.k.a nested mode

Let's create a `add_tag` decorator, that will simply add a new attribute on the decorated function:

```python
from decopatch import function_decorator

@function_decorator
def add_tag(tag='hi!'):
    """
    Example decorator to add a 'tag' attribute to a function. 
    :param tag: the 'tag' value to set on the decorated function (default 'hi!).
    """
    def _apply_decorator(f):
        """
        This is the method that will be called when `@add_tag` is used on a 
        function `f`. It should return a replacement for `f`.
        """
        setattr(f, 'tag', tag)
        return f
    return _apply_decorator
```

Apart from the new `@function_decorator`, it should look very familiar to those of you who tried to write decorators using the native python mechanisms. **Except** that it works out of the box with and without parenthesis, with and without arguments:

```python
@add_tag  # no parenthesis
def foo():
    pass
assert foo.tag == 'hi!'

@add_tag()  # empty parenthesis
def foo():
    pass
assert foo.tag == 'hi!'

@add_tag('hello')  # with args
def foo():
    pass
assert foo.tag == 'hello'

add_tag()(foo)  # manual decoration
assert foo.tag == 'hi!'  
```

Besides, its signature and docstring are preserved:

```python
print("%s%s" % (add_tag.__name__, signature(add_tag)))
print(help(add_tag))
```

yields

```bash
add_tag(tag='hi!')
Help on function add_tag in module decopatch.tests.test_doc:

add_tag(tag='hi!')
    Example decorator to add a 'tag' attribute to a function.
    :param tag: the 'tag' value to set on the decorated function (default 'hi!).
```

Finally note that `_apply_decorator` *can* return a wrapper, but is not forced to: you are free to return `f`, a wrapper of `f`, or a complete replacement for `f`, not even a function! This is the default python language capability, but we tend to forget it when we use `wrapt` or `decorator` because they are designed for wrappers.

### 2- More compact: flat mode

To ease code readability, `decopatch` also supports a *flat* mode:

```python
from decopatch import function_decorator, DECORATED

@function_decorator
def add_tag(tag='hi!', f=DECORATED):
    """
    Example decorator to add a 'tag' attribute to a function.
    :param tag: the 'tag' value to set on the decorated function (default 'hi!).
    """
    setattr(f, 'tag', tag)
    return f
```

As you can see, in that mode you can use one less level of nesting. You indicate which argument is the decorated object by using the `DECORATED` default value. 

But the cool thing is that using this development style does not change the signature that gets exposed to your users: they do not see the `DECORATED` argument, you can check it with `help(add_tag)`! Of course you should not mention it in the docstring.


### 3- Creating function wrappers

A very popular use case for decorators is to create signature-preserving function wrappers. The great [`decorator`](https://github.com/micheles/decorator) library in particular, provides tools to solve this problem "all at once" (decorator + signature-preserving wrapper).

With `decopatch` and its optional companion [`makefun`](https://smarie.github.io/python-makefun/), each problem is now solved in a dedicated library, because the author believes that these are two completely independent problems.

 - `decopatch` (this library) focuses on helping you create decorators that nicely handle the without-parenthesis case. You can decorate functions and classes, and your decorator is free to return anything (the same object that was decorated, a wrapper, or another object).
 - [`makefun`](https://smarie.github.io/python-makefun/) can be used to generate functions with any signature dynamically ; in particular its `@wraps` decorator makes it very easy to create signature-preserving wrappers. It relies on the same tricks than [`decorator`](https://github.com/micheles/decorator) to perform the function generation, but also supports more complex use cases such as signature modification. It can be used anywhere of course, it is not specific to decorators.
 
Both work well together of course:

```python
from decopatch import function_decorator, DECORATED
from makefun import wraps

@function_decorator
def say_hello(person="world", f=DECORATED):
    """
    This decorator modifies the decorated function so as to print a greetings 
    message before each execution.

    :param person: the person name in the print message. Default = "world"
    """
    # (1) create a wrapper of f that will do the print before call
    @wraps(f)  # rely on `makefun` to preserve signature of `f`
    def new_f(*args, **kwargs):
        print("hello, %s !" % person)  # say hello
        return f(*args, **kwargs)      # execute f

    # (2) return it as a replacement for `f`
    return new_f
```

Once again, you can check that all call modes are properly implemented:

```python
@say_hello  # no parenthesis
def foo():
    print("<executing foo>")
foo()

@say_hello()  # empty parenthesis
def bar():
    print("<executing bar>")
bar()

@say_hello("you")  # arg
def custom():
    print("<executing custom>")
custom()

# manual decoration
def custom2():
    print("<executing custom2>")
    
custom2 = say_hello()(custom2)
custom2()
```

yields

```bash
hello, world !
<executing foo>
hello, world !
<executing bar>
hello, you !
<executing custom>
hello, world !
<executing custom2>
```

As stated previously, you can use any other means to generate your function wrapper at step (1) of this example, such as `functools.wraps`, etc. But beware that not all of them are signature-preserving!

#### ...even simpler ?

If you **really** want to avoid nesting in the above example (and take the risk of making your code less readable), `decopatch` supports a double-flat mode:

```python
from decopatch import function_decorator, WRAPPED, F_ARGS, F_KWARGS

@function_decorator
def say_hello(person="world", f=WRAPPED, f_args=F_ARGS, f_kwargs=F_KWARGS):
    """
    This decorator modifies the decorated function so as to print a greetings 
    message before execution.

    :param person: the person name in the print message. Default = "world"
    """
    print("hello, %s !" % person)  # say hello
    return f(*f_args, **f_kwargs)      # execute f
```

This syntax is completely equivalent to the one shown previously. You can check it:

```python
@say_hello  # no parenthesis
def add_ints(a, b):
    return a + b
assert add_ints(1, 3) == 4
```

yields

```
hello, world !
```

As you can see above, the principles of this syntax are simple: all arguments are decorator arguments, except for the ones with default values `WRAPPED` (the decorated item), `F_ARGS` and `F_KWARGS` (the `*args` and `**kwargs` of each function call).


### 4- Decorating classes

You can similarly use `@class_decorator` to create a decorator that works for classes.

Both `@function_decorator` and `@class_decorator` are actually user-friendly presets for the more generic `@decorator` function. So if you wish to write a decorator that can be used both for functions and classes, use `@decorator`:

```python
from decopatch import decorator

@decorator
def add_tag(tag='hi!'):
    """
    Example decorator to add a 'tag' attribute to a function or class.
    :param tag: the 'tag' value to set on the decorated item (default 'hi!).
    """
    def _apply_decorator(o):
        """
        This is the method that will be called when your decorator is used on a
        class or function `o`. It should return the replacement for this object.
        """
        setattr(o, 'tag', tag)
        return o
    return _apply_decorator
```

## How does it work ?

There is no magic here. Without language modification (see [proposal](./pep_proposal)) or additional knowledge or source code introspection, python is just **not capable** of detecting that `@say_hello(foo)` is different from `@say_hello` applied to function `foo`.

However in most standard cases there are well-known "tricks" to perform a disambiguation that covers most standard cases. `decopatch` is basically a collection of such tricks. Some of them are static, based on your decorator's signature, and some others are dynamic, based on the received arguments. See [disambiguation details](./disambiguation) for the complete list and for advanced usage.

## See Also

 - [PEP318](https://www.python.org/dev/peps/pep-0318/) decorators for functions and methods
 - [PEP3129](https://www.python.org/dev/peps/pep-3129/) decorators for classes
 - [decorator](https://github.com/micheles/decorator), the reference library for creating decorators in python. I used it a lot before writing `makefun` and `decopatch`, big thanks to [`micheles`](https://github.com/micheles) !
 - [tutorial 1](https://realpython.com/primer-on-python-decorators/)
 - [tutorial 2](https://www.thecodeship.com/patterns/guide-to-python-function-decorators/)
 - [tutorial 3](http://coderazzi.net/tnotes/python/decoratorsWithoutArguments.html)
 - [tutorial 4](https://www.saltycrane.com/blog/2010/03/simple-python-decorator-examples/)
 - [decorator recipes](https://wiki.python.org/moin/PythonDecoratorLibrary)


### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-decopatch](https://github.com/smarie/python-decopatch)
