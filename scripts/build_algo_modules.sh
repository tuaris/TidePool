#!/bin/sh
cd ../lib/algo/ltc_scrypt
python setup.py build_ext --inplace
python setup.py clean

cd ../yac_scrypt
python setup.py build_ext --inplace
python setup.py clean

cd ../mrc_scrypt
python setup.py build_ext --inplace
python setup.py clean

cd ../thor_scrypt
python setup.py build_ext --inplace
python setup.py clean

cd ../quark
python setup.py build_ext --inplace
python setup.py clean

cd ../max_hash
python setup.py build_ext --inplace
python setup.py clean

cd ../vtc_scrypt
python setup.py build_ext --inplace
python setup.py clean

cd ../sha3
python setup.py build_ext --inplace
python setup.py clean

cd ../../../scripts