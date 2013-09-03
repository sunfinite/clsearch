# -*- coding: utf-8 -*-
import unittest
import sys
import os
import re
sys.path.insert(0, os.path.abspath("../.."))
from test_base import BaseTests
from test_index import IndexTests
from clsearch.search import Search 
import cStringIO

class SearchTests(IndexTests):
    def setUp(self):
        IndexTests.setUp(self)
        self.s = Search(dbPrefix = ".", fout = self.out)

    def test_search_by_type(self):
        files = map(lambda x: os.path.join(os.path.abspath('data'), x), os.listdir("data/"))
        jpgfiles = []
        for file_ in files:
            if re.search("jpg$", file_):
                jpgfiles.append(file_)
        self.test_add_to_index_quiet()
        self.s.search(".jpg")
        output = self.out.getvalue()
        output = output[output.find("Filetype Results:"):]
        for file_ in jpgfiles:
            self.assertTrue(file_ in output)
        
    def test_search_no_results(self):
        self.test_add_to_index()
        self.s.search("should~not!##be__there")
        output = self.out.getvalue()
        self.assertTrue("0 results" in output)
        
if __name__ == "__main__":
    unittest.main()
