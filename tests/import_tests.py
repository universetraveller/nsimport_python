import nsimport
import unittest

class NsImporterTest(unittest.TestCase):

    def test_init_nsimporter(self):
        import sys
        inst = nsimport.NsImporter(sys)
        inst.import_module('sys')
        self.assertIsInstance(inst, nsimport.NsImporter)

    def test_get_importer(self):
        import sys
        inst = nsimport.get_NsImporter([])
        self.assertEqual(sys.path, inst.sys.path)

    def test_copy_function(self):
        def func(a, b):
            return a
        import for_test_module
        f = func
        g = nsimport.copy_function(f, {'new_global':for_test_module}, for_test_module)
        self.assertNotEqual('for_test_module', f.__module__)
        self.assertIsNone(f.__globals__.get('new_global', None))
        self.assertNotEqual(f, g)
        self.assertEqual('for_test_module', g.__module__)
        self.assertEqual('for_test_module', g.__globals__['new_global'].__name__)

    def test_override_functions(self):
        import for_test_module
        self.assertIsNone(for_test_module.func_to_test.__globals__.get('new_global', None))
        for_test_module = nsimport.override_functions(for_test_module, {'new_global':123})
        self.assertIsNotNone(for_test_module.func_to_test.__globals__.get('new_global', None))
        self.assertEqual(123, for_test_module.func_to_test.__globals__['new_global'])

    def test_load_single_module(self):
        import sys
        sys.modules.pop('for_test_module', None)
        inst = nsimport.get_NsImporter(['./'])
        m = inst.import_module('for_test_module')
        self.assertNotIn('for_test_module', sys.modules)
        self.assertIn('for_test_module', inst.sys.modules)
        self.assertEqual(1, m.return1())
    
    def test_load_multi_modules(self):
        import sys
        sys.modules.pop('for_test_module', None)

        inst = nsimport.get_NsImporter(['./'])
        inst1 = nsimport.get_NsImporter(['./'])
        m = inst.import_module('for_test_module')
        m1 = inst1.import_module('for_test_module1')

        self.assertNotIn('for_test_module', sys.modules)
        self.assertNotIn('for_test_module', inst1.sys.modules)
        self.assertIn('for_test_module', inst.sys.modules)

        self.assertNotIn('for_test_module1', sys.modules)
        self.assertNotIn('for_test_module1', inst.sys.modules)
        self.assertIn('for_test_module1', inst1.sys.modules)

        self.assertEqual(1, m.return1())
        self.assertEqual(2, m1.return_same(2))

    def test_cross_before_and_after_import_0(self):
        import sys
        sys.modules.pop('difflib', None)
        sys.modules.pop('datetime', None)

        inst = nsimport.get_NsImporter(['./'])
        inst1 = nsimport.get_NsImporter(['./'])
        m1 = inst1.import_module('difflib')
        m = inst.import_module('datetime')

        self.assertNotIn('difflib', sys.modules)
        self.assertNotIn('_datetime', sys.modules)
        self.assertNotIn('datetime', sys.modules)

        self.assertNotIn('datetime', inst1.sys.modules)
        self.assertNotIn('_datetime', inst1.sys.modules)
        self.assertIn('difflib', inst1.sys.modules)

        self.assertNotIn('difflib', inst.sys.modules)
        self.assertIn('datetime', inst.sys.modules)
        self.assertIn('_datetime', inst.sys.modules)

    def test_cross_before_and_after_import_1(self):
        import sys
        sys.modules.pop('difflib', None)
        sys.modules.pop('datetime', None)
        
        inst = nsimport.get_NsImporter(['./'])
        m = inst.import_module('datetime')
        inst1 = nsimport.get_NsImporter(['./'])
        m1 = inst1.import_module('difflib')

        self.assertNotIn('difflib', sys.modules)
        self.assertNotIn('_datetime', sys.modules)
        self.assertNotIn('datetime', sys.modules)

        self.assertNotIn('datetime', inst1.sys.modules)
        self.assertNotIn('_datetime', inst1.sys.modules)
        self.assertIn('difflib', inst1.sys.modules)

        self.assertNotIn('difflib', inst.sys.modules)
        self.assertIn('datetime', inst.sys.modules)
        self.assertIn('_datetime', inst.sys.modules)

    def test_import_sub_packages(self):
        import sys
        inst = nsimport.get_NsImporter(['./dir0'])
        inst1 = nsimport.get_NsImporter(['./'])
        m = inst.import_module('for_test_module_dir0')
        with self.assertRaises(ModuleNotFoundError):
            m1 = inst1.import_module('for_test_module_dir0')
        m1 = inst1.import_module('dir0.for_test_module_dir0_1')

        self.assertNotIn('for_test_module_dir0', sys.modules)
        self.assertNotIn('for_test_module_dir0_1', sys.modules)
        self.assertIn('for_test_module_dir0', inst.sys.modules)
        self.assertIn('dir0.for_test_module_dir0_1', inst1.sys.modules)

        self.assertEqual(1, m.defined_in_sub_import)
        self.assertEqual(1, m1.defined_in_sub_import)
        self.assertEqual(2, m.return_same(2))

    def test_recursive_import(self):
        import sys
        sys.modules.pop('ftplib', None)
        sys.modules.pop('pdb', None)
        inst = nsimport.get_NsImporter(['./'])
        m = inst.import_module('ftplib')
        m = inst.import_module('pdb')
        self.assertNotIn('ftplib', sys.modules)
        self.assertIn('ftplib', inst.sys.modules)
        self.assertNotIn('pdb', sys.modules)
        self.assertIn('pdb', inst.sys.modules)

    def test_import_same_name_builtin_module(self):
        import sys
        sys.modules.pop('_sre', None)
        inst = nsimport.get_NsImporter(['./'])
        meta_path = inst.sys.meta_path.copy()
        inst.sys.meta_path = [meta_path[2], meta_path[0], meta_path[1]]
        self.assertNotIn('_sre', inst.sys.modules)
        m = inst.import_module('_sre')
        import _sre
        sys.modules['_sre'] = __import__('_sre')
        self.assertNotEqual(id(sys.modules['_sre']), id(m))
        self.assertEqual('my _sre', m.return_same('my _sre'))
        self.assertIsNone(getattr(sys.modules['_sre'], 'return_same', None))

    def test_import_same_name_common_module(self):
        import sys
        sys.modules.pop('cgitb', None)
        inst = nsimport.get_NsImporter(['./dir0'])
        meta_path = inst.sys.meta_path.copy()
        inst.sys.meta_path = [meta_path[2], meta_path[0], meta_path[1]]
        self.assertNotIn('cgitb', inst.sys.modules)
        m = inst.import_module('cgitb')
        import cgitb
        self.assertNotEqual(id(sys.modules['cgitb']), id(m))
        self.assertEqual('my cgitb', m.return_same('my cgitb'))
        self.assertIsNone(getattr(sys.modules['cgitb'], 'return_same', None))

    def test_issue_pre_loaded_modules(self):
        # import enum before importing socket, and socket uses enum.IntEnum that uses global sys as namespace's sys
        import enum
        import sys
        sys.modules.pop('socket', None)
        inst = nsimport.get_NsImporter(['./dir0'])
        m = inst.import_module('socket')

    def test_issue_pre_loaded_modules_solved_no_leakage(self):
        import enum
        import sys
        sys.modules.pop('socket', None)
        inst = nsimport.get_NsImporter(['./dir0'])
        m = inst.import_module('socket')
        self.assertEqual(id(enum), id(sys.modules['enum']))
        self.assertNotEqual(id(enum), id(inst.sys.modules['enum']))
        self.assertEqual(id(inst.sys), id(inst.sys.modules['enum'].sys))

if __name__ == '__main__':
    unittest.main()
