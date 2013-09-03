# -*- coding: utf-8 -*-
from __future__ import division
import os
import sqlite3
import re
import sys

class Base(object):
    """
        Provides helper functions to both Index and Search
    """
    def __init__(self, dbPrefix = None, fout = sys.stdout):
        """
            Creates the sqlite database if not already present.
            Input:
                dbPrefix: The directory where the database will be created.
                          Defaults to ~/.clsearch.
                fout: Write all output to this stream. Defaults to stdout

            *Schema:
                -Media:
                    +path: the absolute path to the file
                    +format: extensions. Makes for faster search by type.
                
                -Words:
                    +word: unicode string
                    +df: document frequency. Incremented for each occurence 
                        of the word. Used as IDF in TF-IDF

                -Tags:
                    +tag: tag name. Either id3 or xmp.

                -Frequency:
                    +wordid: Foreign key to the Words table
                    +mediaid: Foreign key to the Media table
                    +tagid: Foreign key to the Tags table
                    +frequency: term frequency(TF). normalized frequency of word
                                in the string being indexed. Calculated as:
                                number of occurences of word in string /
                                length of string

                                Note:
                                String can be file name or tag values
                                tagid is 0 for words appearing in file name.  
        """ 
        if dbPrefix:
            dbPrefix = os.path.abspath(dbPrefix)
        else:
            dbPrefix = os.path.expanduser("~")

        dbPrefix = os.path.join(dbPrefix, '.clsearch')

        db =  os.path.join(dbPrefix, 'clsdb.sqlite')
        isFirst = False
        if not os.path.exists(db):
            if not os.path.exists(dbPrefix):
                os.mkdir(dbPrefix)
            isFirst = True

        self.fout = fout

        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

        if isFirst:
            self.__create_db()

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.commit()
            self.conn.close()

    def __create_db(self):
        self.cur.execute("create table Media (path string, format string)")
        self.cur.execute("create table Words (word string,\
        df int default 1 not null)")
        self.cur.execute("create table Tags (tag string)")
        self.cur.execute("create table Frequency (wordid int,\
        mediaid int, tagid int, frequency float)")
        self.conn.commit()

    def get_split_string(self):
        """
            Splitting on [\W_]+ causes loss of characters because re
            in 2.x considers combining forms in unicode to be non-alphanumeric

        Eg: 1.  In [34]: re.split(ur"[\W_]+", 'Sigur Rós')
                Out[34]: ['Sigur', 'R', 's']

            2.  In [42]: split_string = i.get_split_string()

                In [43]: re.split(split_string, 'Sigur Rós')
                Out[43]: ['Sigur', 'R\xc3\xb3s']

            Although this solution is crude, it should work in most of the
            cases.

            Builds and returns a string consisting of all non-alphanumeric 
            characters from ASCII 0 to 126 
        """
        split_string = ur''
        for i in range(0, 48):
            split_string += chr(i)
        for i in range(58, 65):
            split_string += chr(i)
        for i in range(91, 97):
            split_string += chr(i)
        for i in range(123, 127):
            split_string += chr(i)

        split_string = re.escape(split_string)
        return "[" + split_string + "]+"

    def to_unicode(self, str_):
        """
            The standard unicode function was not 
            sufficient because of the odd file encoded in 
            latin-1

            Takes a <type 'str'> and returns a <type 'unicode'>
            by trying to decode it using utf-8 or latin-1
        """
        try:
            str_ = str_.decode("utf-8")
        except UnicodeDecodeError:
            try:
                str_ = str_.decode("latin-1")
            except UnicodeDecodeError:
                str_ = str_.decode("utf-8", errors = "ignore")
        except UnicodeEncodeError:
            str_ = str_.decode("utf-8", errors = "replace")
        return str_

