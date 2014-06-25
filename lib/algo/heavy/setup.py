#!/usr/bin/python

import os
from distutils.core import setup, Extension

os.environ['CC'] = 'g++'; os.environ['CXX'] = 'g++';

heavycoin_hash_module = Extension('heavycoin_hash',
                                  sources = ['heavycoinmodule.c',
                                             'heavy.cpp',
                                             'hefty1.cpp',
		                             'sha3/blake.c',
					     'sha3/groestl.c',
					     'sha3/keccak.c'],
                                  include_dirs=['.', './sha3'],
                                  libraries = ['ssl','crypto']
)

setup (name = 'heavycoin_hash',
       version = '1.0',
       description = 'Bindings for proof of work hash used by Heavycoin',
       ext_modules = [heavycoin_hash_module])
