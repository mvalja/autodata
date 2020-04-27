from distutils.core import setup
from Cython.Build import cythonize


setup(
  #name = 'preprocess4_Arango_LCA',
  #ext_modules = cythonize("preprocess4_Arango_LCA.pyx"),
  #name = 'preprocess3_LTM',
  #ext_modules = cythonize("preprocess3_LTM.pyx"),
  name = 'LCA3_quick',
  ext_modules = cythonize("LCA3_quick.pyx"),
  #name='preprocess',
  #ext_modules=cythonize("preprocess.pyx"),
)
"""
setup(
  name = 'preprocess',
  ext_modules = cythonize("preprocess.pyx"),
  #name = 'preprocess3_LTM',
  #ext_modules = cythonize("preprocess3_LTM.pyx"),
  name = 'LTMv5',
  ext_modules = cythonize("LTMv5.pyx"),
)
"""