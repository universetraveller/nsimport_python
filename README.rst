===================================================================================================
nsimport: Import modules to independent namespaces (not load to sys.modules) with modified difflib.
===================================================================================================

With creating individual namespaces for python import mechanism, we can use NsImporter to load modules without conflict, loading modules to different namespaces (not inject them into global namespace). 

All modules loaded by NsImporters will be added to NsImporter's own namespace (access with self.sys), and sys.module contains no them.  

So we can import our modules without conflict such as modules with same name, different packages versions or other situations we do not want loaded modules present in sys.modules.  

This library is modified from `importlib <https://github.com/python/cpython/tree/3.8/Lib/importlib>`_ of python3.8, but there are only 2 differences between nsimport and importlib:

        * __init__.py of importlib is edited to be nsimporter_internal.py by creating a class type to implement namespace initializing before being used to import modules. The class is initialized by set namespace's sys to parameter ``sys`` passed to it.  

        * new __init__.py for whole library.  

----
APIs
----
All available defined APIs can be found in __init__.py and nsimporter_internal.py.  

But it is disencouraged to directly use APIs except ``nsimport.get_NsImporter(path: list)`` which returns a new NsImporter initialized with a copied sys module.  

If you know exactly what module sys do when interpreter imports modules, you can create your own namespace and pass it to ``nsimport.NsImporter(sys)`` and it will be use to initialize the importer.  

Different NsImporters have different namespaces (if different sys modules are passed to it), so it is feasible to use 2 or more importer at the same time.  

You can access namespace's ``sys`` module by accessing instance's member ``sys`` using ``self.sys``, and access namespace's importlib bootstrap using ``self._bootstrap`` and ``self._bootstrap_external``.  

----------
Parameters
----------

* ``nsimport.get_NsImporter(path: list)`` 

        ``path`` is a python list that indicates folders PathFinder use to find modules.  
        Inside the importer, self.sys.path will be assigned ``path + sys.path``, and it acts as sys.path in importer's own namespace.  

* ``nsimport.NsImporter(sys: module)``

        ``sys`` is a module with attributes sys.path, sys.modules, sys.meta_path, sys.path_hooks and sys.path_importer_cache = {}. All of these  attributes should be independent to sys of global namespace, otherwise the importer will still add module to global sys.modules.  

        ``nsimport.get_NsImporter`` provides a convenient way to create needed ``sys`` and passes it to NsImporter to create instance.  

-------
Example
-------
.. code-block:: python

        >>> import nsimport
        >>> importer = nsimport.get_NsImporter([])
        >>> importer
        <nsimport.nsimporter_internal.implib object at 0x7fae0568fdc0>
        >>> importer.import_module('os')
        <module 'os' from '/usr/local/lib/python3.8/os.py'>
        >>> importer.import_module('codeop')
        <module 'codeop' from '/usr/local/lib/python3.8/codeop.py'>
        >>> 'codeop' in sys.modules
        False
        >>> 'codeop' in importer.sys.modules
        True

------
Notice
------
For every NsImporter has its own namespace, all modules loaded by now loading module will be injected to NsImporter's sys.modules but global sys.modules.  

Only test on python3.8, and you can run script `import_tests.py <./tests/import_tests.py>`_ to check if the library works.  

Though try best to make sure the modules in sys.modules are isolated to namespace's sys.modules, modules imported before importing _bootsrap_external may still use global sys in its namespace. Not essential modules before _bootstrap_external are removed with function ``convert_modules_sys`` in `nsimporter_internal.py <./nsimport/nsimporter_internal.py>`_, and other modules will be copied and set new sys module. Unit test ``test_issue_pre_loaded_modules`` and ``test_issue_pre_loaded_modules_solved_no_leakage`` are for this problem. Another implementation does not face this problem.   

Details of implementation are in function `nsimporter_internal.implib.__init__ <./nsimport/nsimporter_internal.py>`_ which replaces sys module of namespaces of _bootstrap functions with its own sys.  

-------
Advance
-------
Another implementation of namespace specific importer is in `moduleimporter <https://github.com/universetraveller/moduleimporter_python>`_, and it provide more general apis, wrapper objects, and reflection mechanism for python modules.  
