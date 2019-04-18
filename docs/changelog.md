# Changelog

### 1.4.5 - Performance improvement

 * Huge performance improvement for the `enable_stack_introspection=True` mode. It also now supports classes correctly.

### 1.4.4 - Reverted varpositional bugfixes now that they are handled in makefun

### 1.4.3 - Bugfix in nested mode under python 2

In python 2, when nested mode was used in a context where the signature contains a var-positional argument, a `TypeError` was raised ; this is now fixed. Fixes [#13](https://github.com/smarie/python-decopatch/issues/13).

### 1.4.2 - Bugfix in flat mode under python 2

In python 2, when flat mode was used in a context where the signature contains a var-positional argument, the arguments were not correctly injected. Fixes [#12](https://github.com/smarie/python-decopatch/issues/12).

### 1.4.1 - Minor default symbols improvement

Removed the clunky `Enum` for symbols. Back to a normal class, with a custom `__repr__`.

### 1.4.0 - Minor dependency version update

Now relying on `makefun>=1.5.0` where arg names changed a bit.

### 1.3.0 - Predefined disambiguators and init file fix

 - We now provide predefined disambiguators `with_parenthesis` and `no_parenthesis`. Fixes [#8](https://github.com/smarie/python-decopatch/issues/8).

 - Fixed `KeyError` when the signature contains `**kwargs`. Fixes [#9](https://github.com/smarie/python-decopatch/issues/9).

 - Fixed issue when the signature only contains `**kwargs`. Fixes [#10](https://github.com/smarie/python-decopatch/issues/10)

 - Fixed static checker problem in PyCharm with the symbols (it came back when we moved to an Enum)

 - Improved exception re-raising in flat mode.

 - Minor: fixed init file.

### 1.2.1 - Flat and double flat symbols: additional protection and bugfix

Default-value symbols `DECORATED`, `WRAPPED`, `F_ARGS` and `F_KWARGS` now have a nicer representation. Fixes [#7](https://github.com/smarie/python-decopatch/issues/7).

When a symbol is used in a signature where it can not be safely injected as keyword argument, an `InvalidSignatureError` is now raised. Fixes [#6](https://github.com/smarie/python-decopatch/issues/6).

### 1.2.0 - Dependency update for important fix

`makefun>=1.4.0` is now required, as it fixes a major issue: [#5](https://github.com/smarie/python-decopatch/issues/5)

### 1.1.1 - Symbols are not classes anymore

Default-value symbols `DECORATED`, `WRAPPED`, `F_ARGS` and `F_KWARGS` are now objects and not classes any more. This prevents IDE to flag the corresponding argument as being misused (not iterable...). Fixes [#4](https://github.com/smarie/python-decopatch/issues/4).

### 1.1.0 - Dependency update

The double-flat mode now relies on `@makefun.wraps`, from `makefun>=1.3.0`. Fixes [#3](https://github.com/smarie/python-decopatch/issues/3).
Updated documentation accordingly.

### 1.0.0 - Refactoring + New "double-flat" mode + API changes + documentation

**API changes:**

 - Added support for a new "double-flat" mode so that users can create decorators creating *signature-preserving function wrappers* with zero level of nesting. Fixes [#2](https://github.com/smarie/python-decopatch/issues/2).
 - Generated var-positional name for kw-only methods is now `'*_'`
 - `can_first_arg_be_ambiguous` parameter removed completely, it was too complex to use.
 - `callable_or_cls_firstarg_disambiguator` renamed `custom_disambiguator` to be more intuitive
 - `wraps` argument renamed `flat_mode_decorated_name`. It was too similar to the wording used in functools, and specific to the flat mode only. Fixes [#1](https://github.com/smarie/python-decopatch/issues/1).

**Improved behaviour**

 - Now the flat mode behaves exactly like nested mode concerning signature-related `TypeError`. This is because when you use the flat mode we now generate a nested mode function with a true signature.
 - Now the exposed decorator uses the `__wrapped__` trick to expose 

**Major refactoring for code readability:**
 
 - Submodules are now consistent and readable. In particular `utils_disambiguation` now provides a clear `disambiguate_call` method, and `util_modes` provides a clear `make_decorator_spec` to handle all the per-mode specificity and always come back to a nested case before going further.
 - removed a case in the `main` module (var-positional) as it was completely covered by the general case.
 - Information is now passed as objects through the various functions, using two main classes `SignatureInfo` (for static information) and `DecoratorUsageInfo` (for dynamic/usage information). The information is computed in a lazy way for each to avoid unnecessary signature binding for example.

**Major documentation update.**

### 0.5.0 - First version

Fully functional with 100+ tests.
