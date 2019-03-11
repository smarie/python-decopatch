# Changelog

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
