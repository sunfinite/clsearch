CLSearch
========

Description
------------
clsearch indexes files of the specified types(and the default types: mp3,aac,ogg,avi,mkv,mp4) and makes it easy to search for these files by name or metadata(currently id3 and xmp).

The results are ranked using TF-IDF scores with results split into filetype results(ex. search ".mp3"), 
direct results(query terms in name of the file) and tag results(query terms in any of the metadata tags)

Tested with python 2.6.5 and python 2.7.5 on linux.

Installation
-------------
::
       
    From source:

    Package is located in dist/clsearch*.tar.gz on github
    (NOTE: Hit view raw and download)

    #python setup.py install
    
    or
    
    From PyPI:

    #pip install clsearch

    
XMP metadata:
----------------
::

    #pip install python-xmp-toolkit 

    This in turn needs exempi. On Ubuntu:

    #apt-get install libexempi3
    
Usage:
------ 
::

    $clsearch -i|--index [-d|--dir <directory>] [-t|--types <types>] [-q|--quiet] 
    $clsearch -s|--search <query>
    $clsearch -h|--help

    Examples:
        $clsearch -i
        $clsearch -i -d /home/example/Music/Awesome/
        $clsearch -i -t flv,txt
        $clsearch -i -t "flv txt jpg"
        
        $clsearch -s lazarus
        $clsearch -s "rock and roll"

    Note:
        1. For xmp tags to be indexed, python-xmp-toolkit and it's dependency Exempy 2.1.1 have to be installed.
        2. The indexing operation can be performed any number of times. Only new files are indexed each time.

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -i, --index           Index filename and id3 and xmp tags if present.
                            Searches for new files and indexes them.
      -d DIRECTORY, --dir=DIRECTORY
                            The directory to be searched for files. Defaults to
                            '~' if not specified.
      -t TYPES, --types=TYPES
                            Additional file types to index. By default
                            mp3,aac,ogg,avi,mkv,mp4 files are indexed.
      -s QUERY, --search=QUERY
                            Search and return file paths ranked by TF-IDF.
      -q, --quiet           Don't print indexed files to stdout.  



Tests
-----
Unit tests are located in src/clsearch/test.

Though each test can be run separately, running 
``$python test_search.py``
will run all tests because it inherits from IndexTest
which in turn inherits from BaseTest.

TODO
----
1. Better exception handling
2. Multiprocessing
3. Fuzzy search...search for "DSC" gives results for "DSC_001.jpg" but not "DSC001.jpg"
