from distutils.core import setup, Extension

X11_hash_module = Extension('X11_hash',
                               sources = ['X11module.c',
                                          'X11.c',
										  'sha3/blake.c',
										  'sha3/bmw.c',
										  'sha3/groestl.c',
										  'sha3/jh.c',
										  'sha3/keccak.c',
										  'sha3/skein.c',
										  'sha3/cubehash.c',
										  'sha3/echo.c',
										  'sha3/luffa.c',
										  'sha3/simd.c',
										  'sha3/shavite.c'],
                               include_dirs=['.', './sha3'])

setup (name = 'X11_hashs',
       version = '1.0',
       description = 'Bindings for proof of work used by X11 Coins',
       ext_modules = [X11_hash_module])
