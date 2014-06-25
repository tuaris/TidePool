from distutils.core import setup, Extension

thor_scrypt_module = Extension('thor_scrypt',
                               sources = ['scryptmodule.c',
                                          './scrypt-jane/scrypt-jane.c'],
                               include_dirs=['.', './scrypt-jane', './scrypt-jane/code'])

setup (name = 'thor_scrypt',
       version = '1.0',
       description = 'Bindings for scrypt proof of work used by thorcoin',
       ext_modules = [thor_scrypt_module])
