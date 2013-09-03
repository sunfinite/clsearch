from distutils.core import setup

setup(name = 'clsearch',
    version = '0.1a1',
    description = 'Index and search files from command line, including id3 and xmp tags.',
    author = 'sunny',
    author_email = 'sunfinite@gmail.com',
    url = 'http://github.com/sunfinite/',
    packages = ['clsearch', 'clsearch.test'],
    package_dir = {'clsearch': 'src/clsearch'},
    scripts = ['bin/clsearch']
    )
