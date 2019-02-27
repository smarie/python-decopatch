**TODO**

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


