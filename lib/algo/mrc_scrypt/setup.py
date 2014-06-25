from distutils.core import setup, Extension

mrc_scrypt_module = Extension('mrc_scrypt',
                               sources = ['scryptmodule.c',
                                          './scrypt-jane/scrypt-jane.c'],
                               include_dirs=['.', './scrypt-jane', './scrypt-jane/code'])

setup (name = 'mrc_scrypt',
       version = '1.0',
       description = 'Bindings for scrypt proof of work used by yacoin',
       ext_modules = [mrc_scrypt_module])
