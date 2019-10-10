# PEP proposal draft

As already stated in this documentation, there is as of python 3.7, absolutely no way to detect that the usage of `@say_hello` in:

```python
@say_hello(foo)
def bar():
    pass
```

is different from 

```python
@say_hello
def foo():
    pass
```

As we saw in the [disambiguation principles](../disambiguation/#3-general-case), a library can disambiguate only if the decorator developer provides additional knowledge.

Below are a few ideas that would fix this problem once and for all (hopefully!) directly in the python language instead. Feedback welcome !

## 1- breaking backwards compatibility

The easiest way to fix the no-parenthesis case directly in the language would be to automatically redirect **all** decorator usage without parenthesis, to empty-parenthesis. So if you have a `set_hello_tag(tag='world')` decorator, if you use it without parenthesis:

```python
@set_hello_tag
def foo():
    pass
```

the python language interpreter would interprete it exactly the same way than

```python
@set_hello_tag()
def foo():
    pass
```

In other words, using a decorator with the `@` syntax and without parenthesis would simply be an alias for the same usage with empty parenthesis.

Implementation would therefore be extremely easy: for all decorators, you would always code it in a "nested" way:

```python
def set_hello_tag(tag='world'):
    def decorate(f):
        setattr(f, 'hello', tag)  # set a hello=<tag> tag on the decorated f
        return f
    return decorate
``` 

**Drawbacks**: this change in the python interpreter behaviour would obviously break compatibility for legacy decorators that did not support arguments at all, such as this one:

```python
def set_helloworld_tag(f):
    setattr(f, 'hello', 'world')  # set a hello=world tag on the decorated f
    return f
``` 


## 2- preserving backwards compatibility

If we need to preserve backwards compatibility, then we need to make the new mechanism optional, so that developers explicitly choose to use it.

My suggestion would be to introduce a new `@decorator_factory` decorator in the `stdlib`, that developers would use to declare that they are ok with redirecting all no-parenthesis usages to with-empty-parenthesis usages. Note that I use the term "factory" because [some users](https://stackoverflow.com/questions/28693930/when-to-use-decorator-and-decorator-factory) use it to distinguish between the no-argument ones (decorators) and the with-argument ones (decorator factories).

This is how you would create a `set_hello_tag` decorator:

```python
@decorator_factory
def set_hello_tag(tag='world'):
    def decorate(f):
        setattr(f, 'hello', tag)  # set a hello tag on the decorated f
        return f
    return decorate
```

The explicit `@decorator_factory` annotation would make the interpreter/stdlib redirect all occurences of `@set_hello_tag` (without parenthesis) into explicit `@set_hello_tag()` (with empty parenthesis).

**Notes:** 

 - if this is a too low-level feature it might require a dedicated language symbol instead of a "normal" decorator ; but it seems overkill - it would be better if we can avoid creating a new language element.
 
 - alternatively or in addition, the python `stdlib` could provide a method that would return `True` if and only if a given frame is a no-parenthesis decorator call. This method, for example named `inspect.is_decorator_call(frame=None)`, could then be used by the various helper libraries, including `decopatch`.

**Follow-up**

After proposing the above to the python-ideas mailing list, it seems that people were not as interested as I thought they would be. I therefore proposed a very minimal feature in [the python bug tracker](https://bugs.python.org/issue36553) (the `inspect.is_decorator_call(frame)` option discussed above). At least with this, everyone would be able to solve the issue easily himself, like this:

```python
from inspect import is_decorator_call

def set_hello_tag(tag='world'):
    if is_decorator_call():
        # called without parenthesis!
        # the decorated object is `tag`
        return set_hello_tag()(tag)   # note that `is_decorator_call` should not return True for this call
    else:
        def decorate(f):
            setattr(f, 'hello', tag)  # set a hello tag on the decorated f
            return f
        return decorate
```

Note that `is_decorator_call` should **not** return `True` in **nested** frames, just for the immediate frame in a decorator application.
