# Changelog

### 1.4.9 - New layout and CI + Compatibility fixes.

 - Enabling the "stack introspection" beta feature with `enable_stack_introspection=True` now raises an explicit `NotImplementedError` on python 3.8+. Fixed [#26](https://github.com/smarie/python-decopatch/issues/26).
 
 - Migrated to the new project layout with nox, github-actions and separation of `src` and `tests`. Fixed test suite with `pytest-cases>=3`. Fixed [#24](https://github.com/smarie/python-decopatch/issues/24) and [#20](https://github.com/smarie/python-decopatch/issues/20).

### 1.4.8 - better packaging

 - packaging improvements: set the "universal wheel" flag to 1, and cleaned up the `setup.py`. In particular removed dependency to `six` for setup and added `py.typed` file, as well as set the `zip_safe` flag to False. Removed tests folder from package. Fixes [#19](https://github.com/smarie/python-decopatch/issues/19)

### 1.4.7 - pyproject.toml

[raddessi](https://github.com/raddessi) added a `pyproject.toml` - thanks! Fixed [pytest-cases#65](https://github.com/smarie/python-pytest-cases/issues/65).

### 1.4.6 - Bug fix

Fixed decorated object injection issue when var-positional arguments are located before it in the signature. Fixed [#14](https://github.com/smarie/python-decopatch/issues/14).

Added `__version__` attribute to comply with PEP396, following [this guide](https://smarie.github.io/python-getversion/#package-versioning-best-practices). Fixes [#15](https://github.com/smarie/python-decopatch/issues/15).

PyPI supports markdown via `long_description_content_type`: pypandoc is not required anymore. Thanks [minrk](https://github.com/smarie/python-makefun/pull/44)! 

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
