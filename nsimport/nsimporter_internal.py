import _imp
import types
import warnings
import functools
import copy
import sys
import builtins
import importlib._bootstrap
from importlib._bootstrap import _spec_from_module, module_from_spec
def copy_module(m):
    _m = type(m)(m.__name__)
    for name in dir(m):
        if name == '__dict__':
            continue
        setattr(_m, name, getattr(m, name))
    return _m

def copy_module1(m):
    s = _spec_from_module(m)
    m.__spec__ = None
    s1 = _spec_from_module(m)
    m1 = type(m)(m.__name__)
    importlib._bootstrap._init_module_attrs(s1, m1, override=True)
    if not s1.loader is None:
        if hasattr(s1.loader, 'exec_module'):
            s1.loader.exec_module(m1)
        else:
            s1.loader.load_module(m.__name__)
    m.__spec__ = s
    return m1

def copy_obj(m, d=0):
    _name = getattr(m, '__name__', 'anonymous')
    _m = type(m)(_name)
    for name in dir(m):
        try:
            this = getattr(m, name)
        except AttributeError:
            continue
        if dir(this) == dir(m):
            continue
        if d > 5:
            _obj = this 
        else:
            _obj = copy_obj(this, d+1)
        setattr(_m, name, _obj)
    return _m

class dict1(dict):
    def __setitem__(self, k, v):
        if k == 'math':
            print(sys.modules)
            raise Exception('1')
        super().__setitem__(k, v)

def inspect_sys():
    return inspect_sys1()
    print('math' in sys.modules)
    o = sys.modules.copy()
    sys.modules = dict1()
    for n in o:
        sys.modules[n] = o[n]

def inspect_sys1():
    print('math' in sys.modules)
    sys.modules = dict1(sys.modules)

def reset_sys():
    sys.modules = dict(sys.modules)

def sys_contains(name):
    return f'{id(sys)}: {name in sys.modules}'

def make_ins(path):
    #inspect_sys()
    reset_sys()
    _sys = copy_module(sys)
    _sys.modules = {}
    for i in sys.modules:
        _sys.modules[i] = sys.modules[i]
    _sys.path = sys.path.copy()
    _sys.meta_path  = sys.meta_path.copy()
    _builtins = copy_module(builtins)
    _sys.modules['builtins'] = _builtins
    _sys.path = path.copy() + _sys.path
    ins = implib(_sys)
    return ins

def copy_function(obj, _globals, module):
    g = types.FunctionType(obj.__code__, _globals, name=obj.__name__, argdefs=obj.__defaults__, closure=obj.__closure__)
    h = functools.update_wrapper(g, obj)
    if not h is None:
        g = h
    g.__module__ = module.__name__
    g.__kwdefaults__ = copy.copy(obj.__kwdefaults__)
    return g

def override_functions(module, _globals):
    for name in dir(module):
        obj = getattr(module, name, None)
        if isinstance(module, type) and name ==  '__class__':
            continue
        if isinstance(obj, types.FunctionType):
            setattr(module, name, copy_function(obj, _globals, module))
        elif isinstance(obj, type) and obj is not None:
            setattr(module, name, override_functions(obj, _globals))
        elif isinstance(obj, types.MethodType):
            f = getattr(obj, '__func__')
            g = copy_function(f, _globals, module)
            obj = types.MethodType(g, module)
            setattr(module, name, obj)
        elif isinstance(obj, property):
            f = getattr(obj, 'fget', None)
            if f is not None:
                g = copy_function(f, _globals, module)
                obj = property(g, getattr(obj, 'fset'), getattr(obj, 'fdel', None), '')
                setattr(module, name, obj)

    return module

def set_path_hooks(_sys, _bs, _globals):
    _sys.path_importer_cache = {}
    _new_hooks = []
    _zip = _sys.modules['zipimport'].zipimporter
    _new_hooks.append(_zip)
    _new_hooks.extend([_bs.FileFinder.path_hook(*_bs._get_supported_file_loaders())])
    _sys.path_hooks = _new_hooks

class implib:
    def __init__(self, sys):
        self.sys = sys
        from . import _bootstrap
        _bootstrap_ = copy_module(_bootstrap)

        self._bootstrap = _bootstrap_
        self._bootstrap.__name__ = 'nsimport._bootstrap'
        self._bootstrap.__package__ = 'nsimport'
        self.sys.modules['nsimport._bootstrap'] = self._bootstrap

        self._bootstrap.__builtins__ = self.sys.modules['builtins']
        override_functions(self._bootstrap, self._bootstrap.__dict__)
        self._bootstrap._setup(self.sys, _imp)
        self.sys.modules['builtins'].__dict__['__import__'] = self._bootstrap.__import__
        self.sys.modules['sys'] = self.sys

        _bootstrap_external = self._bootstrap.__import__('nsimport._bootstrap_external')._bootstrap_external
        _bootstrap_external_ = copy_module(_bootstrap_external)
        self._bootstrap_external = _bootstrap_external_
        self._bootstrap._bootstrap_external = self._bootstrap_external
        self._bootstrap_external.__name__ = 'nsimport._bootstrap_external'
        self._bootstrap_external.__package__ = 'nsimport'
        self.sys.modules['nsimport._bootstrap_external'] = self._bootstrap_external
        self._bootstrap_external.__builtins__ = self.sys.modules['builtins']
        override_functions(self._bootstrap_external, self._bootstrap_external.__dict__)
        self._bootstrap_external._setup(self._bootstrap)
        self.sys.modules['zipimport'] = self._bootstrap.__import__('zipimport')
        set_path_hooks(self.sys, self._bootstrap_external, self._bootstrap.__dict__)

        self.sys.meta_path = [self._bootstrap.BuiltinImporter, self._bootstrap.FrozenImporter, self._bootstrap_external.PathFinder]
        self.__import__ = self._bootstrap.__import__



        # Public API #########################################################



    def invalidate_caches(self):
        """Call the invalidate_caches() method on all meta path finders stored in
        sys.meta_path (where implemented)."""
        for finder in self.sys.meta_path:
            if hasattr(finder, 'invalidate_caches'):
                finder.invalidate_caches()


    def find_loader(self, name, path=None):
        """Return the loader for the specified module.

        This is a backward-compatible wrapper around find_spec().

        This function is deprecated in favor of importlib.util.find_spec().

        """
        warnings.warn('Deprecated since Python 3.4. '
                      'Use importlib.util.find_spec() instead.',
                      DeprecationWarning, stacklevel=2)
        try:
            loader = self.sys.modules[name].__loader__
            if loader is None:
                raise ValueError('{}.__loader__ is None'.format(name))
            else:
                return loader
        except KeyError:
            pass
        except AttributeError:
            raise ValueError('{}.__loader__ is not set'.format(name)) from None

        spec = self._bootstrap._find_spec(name, path)
        # We won't worry about malformed specs (missing attributes).
        if spec is None:
            return None
        if spec.loader is None:
            if spec.submodule_search_locations is None:
                raise ImportError('spec for {} missing loader'.format(name),
                                  name=name)
            raise ImportError('namespace packages do not have loaders',
                              name=name)
        return spec.loader


    def import_module(self, name, package=None):
        """Import a module.

        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.

        """
        level = 0
        if name.startswith('.'):
            if not package:
                msg = ("the 'package' argument is required to perform a relative "
                       "import for {!r}")
                raise TypeError(msg.format(name))
            for character in name:
                if character != '.':
                    break
                level += 1
        return self._bootstrap._gcd_import(name[level:], package, level)


    _RELOADING = {}


    def reload(self, module):
        """Reload the module and return it.

        The module must have been successfully imported before.

        """
        if not module or not isinstance(module, types.ModuleType):
            raise TypeError("reload() argument must be a module")
        try:
            name = module.__spec__.name
        except AttributeError:
            name = module.__name__

        if self.sys.modules.get(name) is not module:
            msg = "module {} not in sys.modules"
            raise ImportError(msg.format(name), name=name)
        if name in _RELOADING:
            return _RELOADING[name]
        _RELOADING[name] = module
        try:
            parent_name = name.rpartition('.')[0]
            if parent_name:
                try:
                    parent = self.sys.modules[parent_name]
                except KeyError:
                    msg = "parent {!r} not in sys.modules"
                    raise ImportError(msg.format(parent_name),
                                      name=parent_name) from None
                else:
                    pkgpath = parent.__path__
            else:
                pkgpath = None
            target = module
            spec = module.__spec__ = self._bootstrap._find_spec(name, pkgpath, target)
            if spec is None:
                raise ModuleNotFoundError(f"spec not found for the module {name!r}", name=name)
            self._bootstrap._exec(spec, module)
            # The module may have replaced itself in sys.modules!
            return self.sys.modules[name]
        finally:
            try:
                del _RELOADING[name]
            except KeyError:
                pass
