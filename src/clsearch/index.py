# -*- coding: utf-8 -*-
from __future__ import division
import os
import sys
import re
import time
from clsearch.base import Base

class Index(Base):
    """ 
        - Inherits and extends Base
        - Walks through specified directory. ~ by default
        - Populates database 
        - Extracts metadata tags
    """
    def __init__(self, quiet = False, fileTypes = [], dbPrefix = None, fout = sys.stdout):
        """
            - Checks if xmp libraries are present
            - Calls Base parent class constructor with 
              dbPrefix and fout input options

            Input:
                quiet: Don't display blow-by-blow details of indexing.
                   False by default.
                fileTypes: Additional types to be searched and indexing
                   along with mp3, aac, ogg, avi, mkv and mp4
                dbPrefix: Argument to parent constructor. Specificies the 
                   directory where the sqlite database will be created.
                    ~ by default.
                fout: Argument to parent constructor. Specified stream to which
                    all output will be written to.
        """ 
                 
        try:
            import libxmp as lx
            self.xmp_file_to_dict = lx.utils.file_to_dict
            self.isXMP = True
        except Exception, e:
            fout.write("XMP error: %s, xmp tags will not be indexed.\n"%e)
            self.isXMP = False
        self.quiet = quiet
        self.fileTypes = ["mp3", "aac", "ogg", "avi", "mkv", "mp4"] + fileTypes
        self.counter = 0
        super(Index, self).__init__(dbPrefix, fout)

    def index(self, dirName = None):
        """
            - The function called by the script to index files.
            - Uses os.path.walk to recurse through the directory structure.
            - If a file has any of the given filetypes at the end,
              call add_to_index() with that filename.
            - Measure time taken for the walk function to return, 
              including time to index files.
            - Print summary of indexing: 
               number of files read from the counter class attribute.
            - Reset index counter to 0.

            Input:
                dirName: The directory given as input to
                    os.path.walk. ~ by default.
        """
            
        if dirName:
            dirName = os.path.abspath(dirName)
        dirName = dirName or os.path.expanduser("~")

        def crawl(args, dName, fNames):
            if not self.quiet:
                self.fout.write("Searching %s\n"%dName)
            for fName in fNames:
                if os.path.splitext(fName)[1][1:].strip().lower() in self.fileTypes:
                    self.add_to_index(os.path.join(dName, fName))

        if self.quiet:
            self.fout.write("Indexing...\n")
        start_time = time.time()
        os.path.walk(dirName, crawl, None)
        self.conn.commit()
        end_time = time.time()
        self.__printSummary(end_time - start_time)
        self.counter = 0


    def add_to_index(self, path):
        """
            - Add a given file to the database.
            - Convert filename to unicode string.
            - If file is already in database, return False.
            - If not, add filename to Media table.
            - Add words in filename to Words table.
            - Get id3 and xmp tags.
            - Add tag keys to Tags table.
            - Add words in tag values to Words table.

        Input:
            path: file to be added
        """ 
        path = self.to_unicode(path)
        #FIXME: This splitting is being done twice because of the unicode dilemma
        name, format_ = os.path.splitext(os.path.split(path)[1])

        media_id, created = self.__get_or_create("Media", path = path, format = format_.strip().lower())
        if not created:
             return False
        else:
            self.counter += 1
            if not self.quiet:
                self.fout.write("Indexing %s\n"%path)
            self.__add_string(name, media_id, 0)
            tags = {}
            if self.isXMP:
                tags.update(self.get_xmp_tags(path))
            tags.update(self.get_id3_tags(path))
            for tag, value in tags.items():
                tag_id, created = self.__get_or_create("Tags", tag = tag)
                self.__add_string(value, media_id, tag_id)
            return True

    def __add_string(self, string, media_id, tag_id):
        """
            - Called by add_to_index
            - Adds to Words and Frequency tables
            - Uses get_split_string to split into words
            - Updates document frequency(DF) of word 
        """
        words = filter(lambda x: x.strip(),\
        map(lambda x: x.lower(),\
        #FIXME: re.UNICODE causes weird problems with the new split string
        re.split(self.get_split_string(), string)))
        wRows = [self.__get_or_create("Words", word = word) for word in words]
        for i, w in enumerate(wRows):
            if not w[1]:
                self.cur.execute("update Words set df = df + 1 where word = ?",[words[i]])
            self.cur.execute("insert into Frequency values (?, ?, ?, ?)",\
            [w[0], media_id, tag_id, words.count(words[i]) / len(words)])
            #FIXME: The loop is not entered if wRows is empty..so no worry about zero division?


    def __get_or_create(self, tableName, **colVals):
        """
         A limited imitation of django's similar ORM function
        """
        if not colVals:
            raise Exception("No column values specified")

        query = "select rowid from %s where "%tableName
        query += " and ".join(["%s='%s'"%(k,v.replace("'", "''")) for k, v in colVals.items()])
        self.cur.execute(query)
        row = self.cur.fetchone()
        if row:
            return (row[0], False)

        query = "insert into %s values (%s"%(tableName,\
        ",".join(["'%s'"%col.replace("'", "''") for col in colVals.values()]))
        #FIXME: Hack
        query += tableName == "Words" and ",1)" or ")"
        self.cur.execute(query)
        return (self.cur.lastrowid, True)

    def __printSummary(self, numSeconds):
        """
            - Print number of indexed files in number of seconds
            - Called even in quiet mode
        """
        self.fout.write("-" * 42 + "\n")
        if self.counter == 0:
            self.fout.write("\nNo new media files\n\n")
        else:
            self.fout.write("\nIndexed %d new files in %d seconds\n\n"%(self.counter, numSeconds))
        self.fout.write("-" * 42)

    def get_id3_tags(self, fileName):
        """
            Code taken from 'Dive Into Python' and genre list lookup has been added
             
            Input:
                fileName: get tags for this file 
        """ 
        def stripnulls(data):
            return self.to_unicode(data.replace("\00", "").strip().lower())

        tags = {}
        tagDataMap = {  "title": ( 3, 33, stripnulls),
                        "artist" : ( 33, 63, stripnulls),
                        "album": ( 63, 93, stripnulls),
                        "year": ( 93, 97, stripnulls),
                        "comment" : ( 97, 126, stripnulls),
                        "genre": (127, 128, lambda x: self.to_unicode(genre_list[ord(x) % 149]))
                     }

        genre_list = ['blues', 'classic rock', 'country', 'dance', 'disco', 'funk',
        'grunge', 'hip-hop', 'jazz', 'metal', 'new age', 'oldies', 'other', 'pop',
        'r&b', 'rap', 'reggae', 'rock', 'techno', 'industrial', 'alternative',
        'ska', 'death metal', 'pranks', 'soundtrack', 'euro-techno', 'ambient',
        'trip-hop', 'vocal', 'jazz+funk', 'fusion', 'trance', 'classical',
        'instrumental', 'acid', 'house', 'game', 'sound clip', 'gospel', 
        'noise', 'alternrock', 'bass', 'soul', 'punk', 'space', 'meditative',
        'instrumental pop', 'instrumental rock', 'ethnic', 'gothic', 'darkwave',
        'techno-industrial', 'electronic', 'pop-folk', 'eurodance', 'dream',
        'southern rock', 'comedy', 'cult', 'gangsta rap', 'top 40', 'christian rap',
        'pop / funk', 'jungle', 'native american', 'cabaret', 'new wave',
        'psychedelic', 'rave', 'showtunes', 'trailer', 'lo-fi', 'tribal', 'acid punk',
        'acid jazz', 'polka', 'retro', 'musical', 'rock & roll', 'hard rock', 'folk',
        'folk-rock', 'national folk', 'swing', 'fast  fusion', 'bebob', 'latin',
        'revival', 'celtic', 'bluegrass', 'avantgarde', 'gothic rock',
        'progressive rock', 'psychedelic rock', 'symphonic rock', 'slow rock',
        'big band', 'chorus', 'easy listening', 'acoustic', 'humour', 'speech',
        'chanson', 'opera', 'chamber music', 'sonata', 'symphony', 'booty bass',
        'primus', 'porn groove', 'satire', 'slow jam', 'club', 'tango', 'samba',
        'folklore', 'ballad', 'power ballad', 'rhythmic soul', 'freestyle',
        'duet', 'punk rock', 'drum solo', 'a cappella', 'euro-house', 'dance hall',
        'goa', 'drum & bass', 'club-house', 'hardcore', 'terror', 'indie', 'britpop',
        'negerpunk', 'polsk punk', 'beat', 'christian gangsta rap', 'heavy metal',
        'black metal', 'crossover', 'contemporary christian', 'christian rock',
        'merengue', 'salsa', 'thrash metal', 'anime', 'jpop', 'synthpop', 'rock/pop']

        try:
            if not os.path.isfile(os.path.abspath(fileName)):
                fileName = fileName.encode('latin-1')
            with open(fileName, 'rb') as f:
                f.seek(-128, 2)
                tagData = f.read(128)
                if tagData[:3] == "TAG":
                    for tag, (start, end, parseMethod) in tagDataMap.items():
                        tags[tag] = parseMethod(tagData[start : end])

        except Exception, e:
            if not self.quiet:
                self.fout.write("Skipping %s because of error: %s\n"%(fileName, e))
        return tags

    def get_xmp_tags(self, fileName):
        """
            Input:
                fileName: get tags for this file
        """
        tags = {}
        try:
            #FIXME: Hack for a failing part of the code in utls.py of libxml
            if not os.path.isfile(os.path.abspath(fileName)):
                fileName = fileName.encode('latin-1')
            nSpaces = self.xmp_file_to_dict(file_path = fileName)
            for ns in nSpaces.values():
                for prop in ns:
                    tags[prop[0].split(":")[1].lower().strip()] = prop[1].lower().strip()

        except Exception, e:
            if not self.quiet:
                self.fout.write("Skipping %s because of error: %s\n"%(fileName, e))
        return tags
