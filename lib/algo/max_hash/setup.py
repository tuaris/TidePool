from distutils.core import setup, Extension

max_hash_module = Extension('max_hash',
                               sources = ['maxcoinmodule.c',
                                          'maxcoin.c',
										  'sha3/keccak.c'],
                               include_dirs=['.', './sha3'])

setup (name = 'max_hash',
       version = '1.0',
       description = 'Bindings for keccak proof of work used by Maxcoin',
       ext_modules = [max_hash_module])
