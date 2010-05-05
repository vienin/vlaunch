#!/usr/bin/env python

"""
setup.py file for SWIG clamav
"""

from distutils.core import setup, Extension


clamav_module = Extension('_clamav',
                           sources=['clamav_wrap.c'],
						   include_dirs=['./'],
						   library_dirs=['./'],
						   libraries=['libclamav','libclamunrar']
                           )

setup (name = 'clamav',
       version = '0.1',
       ext_modules = [clamav_module],
       py_modules = ["clamav"]
       )
