# Usage details

**WARNING: THIS IS AN OLD PAGE WITH OUTDATED INFORMATION ! PLEASE IGNORE IT !**


### a- Flat mode

In this mode the decorator is implemented as a function, that should return the replacement for the decorated item. To create a decorator you have to do two things:
 
 - use `@function_decorator`, `@class_decorator` or `@decorator` on your implementation function
 - declare which variable represents the injected decorated item by using the `DECORATED` keyword as its default value. 
 
Note: if you can not or do not want to add the `DECORATED` default value, you can specify the variable name explicitly with `decorated=<argname>`.

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


### c- Advanced topics

1 mandatory


either

```python
InvalidMandatoryArgError: function 'add_tag' requires a mandatory argument 'tag'. Provided value '<function foo at 0x00000160858ED510>' does not pass its validation criteria
``` 

Note that this error is a dedicated subclass of `TypeError`, and not the native `TypeError` that python raises when a function is called without a mandatory argument. This is mostly for testability reasons, to make sure that the library worked correctly.

By default **you cannot use a callable as first mandatory argument**:

```python
@add_tag(print)
def foo():
    return
```

raises

```python
InvalidMandatoryArgError: function 'add_tag' requires a mandatory argument 'tag'. Provided value '<built-in function print>' does not pass its validation criteria
```

Indeed there is absolutely no way in the python language to disambiguate this case with the previous one without user-provided disambiguation rules. Since we wanted to avoid silent incorrect behaviour in the previous (no-parenthesis) usage, then the consequence is that we have an error in this usage that seems legitimate. 

**It is very easy to fix this**: if you wish to accept callables/classes as first mandatory argument, the simplest thing to do is to **force keyword usage** (adding a star as first argument):
 
```python
@function_decorator
def add_tag(*, tag, f=DECORATED):
    """ We use the * in the signature to disambiguate """
    setattr(f, 'my_tag', tag)
    return f
``` 

Now your decorator will be entirely not ambiguous, users will be able to pass callables to it while still getting an error in case they use it without arguments.

```python
@add_tag(tag=print)  # >> disambiguated: now works correctly
def foo():
    return

assert foo.my_tag == print

@add_tag  # >> disambiguated: raises the standard TypeError now
def foo():
    return
```

Note: if you do not want to use this trick, there are other, more cumbersome ways to perform the disambiguation. See [this section on first argument disambiguation]().


1 optional

Let's modify the previous decorator so that its `tag` argument is optional:

```python
@function_decorator
def add_tag(tag='tag!', f=DECORATED):
    setattr(f, 'my_tag', tag)
    return f
```

You see that `decopath` does not accept it:

```python
AmbiguousDecoratorDefinitionError: This decorator is ambiguous because it has only optional arguments. Please provide an explicit protection.
```

Indeed this is a very ambiguous decorator: the decorator 

 - can be used without arguments: `@add_tag` or `@add_tag()`
 - but it can also be used with arguments: `@add_tag('hello')`. In particular it can be used with a callable as first argument such as in `@add_tag(print)`

The python language is not able to see the difference between using `@add_tag` to decorate a function named `print`, and `@add_tag(print)` applied to decorate another function:

```python
# the following two usages are programmatically undetectable
# except if we cheat and look at the source code

@add_tag
def print():
    return

@add_tag(print)
def another():
    return    
```

, and therefore we ask you to explicitly protect your decorator. Once again you can use the "keyword-only" trick, or if you have a good reason not to do it, see [this section on first argument disambiguation]().

Wrapper

Note that this time usage without arguments is permitted, as long as the value provided for the first argument is not a callable - as that would be ambiguous.




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


