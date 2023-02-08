import timeit

read_py = """\
with open('test.csv') as fh:
    x = fh.read()
"""


read_c_setup = """\
import ctypes
import pathlib

libname = pathlib.Path().absolute() / "read.so"
c_lib = ctypes.CDLL(libname)
c_lib.readfile.restype = ctypes.c_char_p
"""
read_c = """\
x = c_lib.readfile(ctypes.c_char_p('test.csv'.encode('utf-8')))
"""

if __name__ == "__main__":
    print("> Python read file")
    print(timeit.timeit(stmt=read_py))

    print("> C read file (unbuffered)")
    print(timeit.timeit(stmt=read_c, setup=read_c_setup))
