# -*- coding: utf-8 -*-
from __future__ import division
import re
import sys
from clsearch.base import Base

class Search(Base):
    """
        - Inherits and extends Base
        - Search a given query, first by type
          and then in name and tags
        - Print output under different sections
    """
    def __init__(self, dbPrefix = None, fout = sys.stdout):
        """
            - Calls Base parent class constructor with 
              dbPrefix and fout input options
              
            Input: 
                dbPrefix: Argument to parent constructor. Specificies the 
                   directory where the sqlite database will be created.
                    ~ by default.
                fout: Argument to parent constructor. Specified stream to which
                    all output will be written to.
        """
        super(Search, self).__init__(dbPrefix, fout)

    def search(self, query):
        """ 
            - First performs search by format
            - If any word begins with a ".", it is considered
              and extension type and searched.
            - normalize_query is then called to get individual
              terms
            - A dictionary is built with hit paths as keys
            - For each path, TF-IDF score is calculated as the sum
              of the TF and 1/DF of each term of the query
              which is a part of the path, either in name or tag.
            - tagSet is a set of all tagids for each path 
            - __print_results function looks up tagids and substitues
              appropriate tag names
            - If 0 is part of tagSet, it is a direct hit

            Input: 
                query who terms should be searched
        """
        results = {}
        noFormatResults = True
        for word in query.split():
            word = word.strip().lower()
            if word[0] == ".":
                if self.search_by_format(word):
                    noFormatResults = False

        for word in self.normalize_query(query):
            word = self.to_unicode(word)
            self.cur.execute("select m.path, f.frequency,  w.df, f.tagid from\
            Media m, Frequency F, Words W where\
            m.rowid = f.mediaid and f.wordid = w.rowid and word = ?", [word])

            for row in self.cur.fetchall():
                path, idf, tag_id = row[0], row[1] * (1 / row[2]), row[3]
                cur, tagSet = results.get(path, [0, set()])
                tagSet.add(tag_id)
                results[path] = [cur + idf, tagSet]

        self.__print_results(results, noFormatResults)

    def __print_results(self, results, noFormatResults):
        """
            Split results into two lists based on 
            0 being present in tagSet.

            0 was used to indicate words appearing in
            the name of a file
        """
        if not results:
            if  noFormatResults:
                self.fout.write("0 results found. Make sure you have indexed the files.\n")
            return

        self.cur.execute("select tag from Tags")
        tagNames = self.cur.fetchall()

        dResults = []
        tResults = []

        for result in  sorted([(k, v) for k, v in results.items()],
        key = lambda x: x[1][0], reverse = True):
            tagSet = result[1][1]
            if 0 in tagSet:
                tagSet.remove(0)
                dResults.append(result)
            else:
                tResults.append(result)

        self.fout.write("\nDirect Results(in name):\n\n")

        for result in dResults:
            self.fout.write(result[0])
            self.fout.write("\n")
            if result[1][1]:
                self.fout.write("Also in tags: %s"\
                % (",".join([tagNames[tag - 1][0] for tag in result[1][1]])))

        print "\nTag Results:\n"

        for result in tResults:
            self.fout.write(result[0])
            self.fout.write("\n")
            self.fout.write("In tags: %s"\
            % ",".join([tagNames[tag - 1][0] for tag in result[1][1]]))


    def normalize_query(self, query):
        """
            - Returns list of individual terms in query
            - Uses the same split string as the index function.

            Input:
                query
        """
        return [word.strip().lower() for word in\
        re.split(self.get_split_string(), query) if word]

    def search_by_format(self, format_):
        """
            Search and print immediately by looking-up 
            format column in Words

            Returns True if there was atleast one hit, used to
            account in the final hit score.
             
            Input:
                format 
        """
        self.cur.execute("select path from Media where format = ?", [format_])
        results =  [file_[0] for file_ in self.cur.fetchall() if file_]
        if results:
            self.fout.write("\nFiletype Results:\n\n")
            for file_ in results:
                self.fout.write(file_)
                self.fout.write("\n")
            return True
        return False
