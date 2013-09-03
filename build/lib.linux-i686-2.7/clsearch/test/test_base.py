# -*- coding: utf-8 -*-
import unittest
import sys
import os
import re
sys.path.insert(0, os.path.abspath("../.."))
from clsearch.base import Base

class BaseTests(unittest.TestCase):
    def setUp(self):    
        self.b = Base()
        self.dbPath = ".clsearch/clsdb.sqlite"

    def test_db_creation(self):
        self.assertRaises(OSError, Base, "/usr")
        Base(".")
        self.assertTrue(os.path.exists(self.dbPath))

    def test_db_deletion(self):
        os.remove(self.dbPath)
        self.assertFalse(os.path.exists(self.dbPath))

        Base(".")
        self.assertTrue(os.path.exists(self.dbPath))

        os.remove(self.dbPath)
        os.rmdir(".clsearch")
        self.assertFalse(os.path.exists(self.dbPath))

        Base(".")
        self.assertTrue(os.path.exists(self.dbPath))
        
        os.remove(self.dbPath)
        os.rmdir(".clsearch")
        self.assertFalse(os.path.exists(self.dbPath))

    def test_to_unicode(self):    
        testStrings  = ["", "hello!~", "\x01\x92"]
        for str_ in testStrings:
            str_ = self.b.to_unicode(str_)
            self.assertEqual(type(str_), unicode)
        
        self.assertRaises(AttributeError, self.b.to_unicode, 123.123)

    def test_get_split_string(self):
        testStrings = {
                    u'uni\u0C80code ,,,, string': [u'uni\u0C80code', u'string'],
                    'Sigur! Rós': ['Sigur', 'Rós'],
                    'Sigur Rós!': ['Sigur', 'Rós', ''],
        }
                    
        for k, v in testStrings.items():
            self.assertEqual(re.split(self.b.get_split_string(), k), v)
        

if __name__ == "__main__":
    unittest.main()
