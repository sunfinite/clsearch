# -*- coding: utf-8 -*-
import unittest
import sys
import os
import re
sys.path.insert(0, os.path.abspath("../.."))
from test_base import BaseTests
from clsearch.index import Index 
import cStringIO

class IndexTests(BaseTests):
    def setUp(self):
        BaseTests.setUp(self)
        self.out = cStringIO.StringIO()
        self.i = Index(quiet = True, dbPrefix = ".", fileTypes = ['jpg'], fout = self.out)

    def test_db_exists(self):
        self.assertTrue(os.path.exists(self.dbPath))
    
    def test_file_types(self):
        self.assertTrue("jpg" in  self.i.fileTypes)

    def test_add_to_index_quiet(self):
        files = os.listdir("data/")
        self.i.index(".")
        output = self.out.getvalue()

        self.assertTrue("Indexing..." in output)

        for file_ in files:
            self.assertFalse(file_ in output)

        self.assertTrue("Indexed %d new files"%len(files) in output)

    def test_add_to_index(self):
        self.i = Index(dbPrefix = ".", fileTypes = ['jpg'], fout = self.out)
        files = os.listdir("data/")
        self.i.index(".")
        output = self.out.getvalue()

        self.assertFalse("Indexing..." in output)

        for file_ in files:
            self.assertTrue(file_ in output)

        self.assertTrue("Indexed %d new files"%len(files) in output)

    def test_db_entries(self):
        self.test_add_to_index_quiet()
        files = map(lambda x: os.path.join(os.path.abspath('data'), x), os.listdir("data/"))
        self.i.cur.execute("select * from Media")
        vals = self.i.cur.fetchall()
        self.assertTrue(vals)

        self.assertEqual(len(vals), len(files))

        for val in vals:
            self.assertTrue(val[0] in files)
        
    def test_get_id3_tags(self):
        test_dict = {'album': u'duet', 
                     'comment': u'', 
                     'title': u'how insensitive', 
                     'artist': u'chick corea & hiromi',
                     'year': u'2008', 'genre': u'other'} 

        self.assertEqual(self.i.get_id3_tags("data/02 How Insensitive.mp3"), test_dict)
        
        
    def test_get_xmp_tags(self):
        if self.i.isXMP:
            test_dict = {u'album': u'duet',
                         u'artist': u'chick corea & hiromi',
                         u'createdate': u'2008',
                         u'title[1]': u'how insensitive',
                         u'tracknumber': u'2',
                         u'genre': u'jazz',
                         u'title': u'',
                         u'discnumber': u'1',
                         u'title[1]/?xml': u'x-default'}
            self.assertEqual(self.i.get_xmp_tags("data/02 How Insensitive.mp3"), test_dict)
        else:
            pass

    def tearDown(self):
        if os.path.exists(self.dbPath):
            os.remove(self.dbPath)
            os.rmdir(".clsearch")
        self.out.close()
        
if __name__ == "__main__":
    unittest.main()
