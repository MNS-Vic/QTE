# coding=utf-8
from __future__ import print_function

import sys
import glob
import os
import shutil
# from distutils.core import setup
# from distutils.extension import Extension
# from distutils.util import get_platform

# from Cython.Distutils import build_ext

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools._distutils.util import get_platform

remove_files = [
    "c_sdk.cpp",
    "c_sdk.pyd",
    "c_sdk.cp36-win32.pyd",
    "c_sdk.cp36-win_amd64.pyd",
    "c_sdk.cp37-win32.pyd",
    "c_sdk.cp37-win_amd64.pyd",
    "c_sdk.cp38-win32.pyd",
    "c_sdk.cp38-win_amd64.pyd",
    "c_sdk.cp39-win32.pyd",
    "c_sdk.cp39-win_amd64.pyd",
    "c_sdk.cp310-win32.pyd",
    "c_sdk.cp310-win_amd64.pyd",
    "c_sdk.cp311-win32.pyd",
    "c_sdk.cp311-win_amd64.pyd",
    "c_sdk.cp312-win_amd64.pyd",
    "c_sdk.cpython-36m-x86_64-linux-gnu.so",
    "c_sdk.cpython-37m-x86_64-linux-gnu.so",
    "c_sdk.cpython-38-x86_64-linux-gnu.so",
    "c_sdk.cpython-39-x86_64-linux-gnu.so",
    "c_sdk.cpython-310-x86_64-linux-gnu.so",
    "c_sdk.cpython-311-x86_64-linux-gnu.so",
    "c_sdk.cpython-312-x86_64-linux-gnu.so",
    "libgm3.so",
    "libgm3-c.so",
    "gmsdk.dll",
    "thostmduserapi_se.dll",
    "thostmd_wrap.dll",
    "libthostmduserapi_se.so",
    "libthostmd_wrap.so",
    "gmpytool.pyd",
    "gmpytool.so",
]
for f in remove_files:
    if os.path.exists(f):
        os.remove(f)

platform = get_platform()
dlllibdir = "./lib/{}".format(platform)
ext_modules = [
    Extension(
        "c_sdk",
        ["c_sdk.pyx"],
        language="c++",
        include_dirs=["./include"],
        library_dirs=[dlllibdir],
        libraries=["gm3-c"],  # so文件的名字去掉前面的lib字样
        extra_link_args=["-Wl,-rpath", "-Wl,$ORIGIN"],
    )
]

setup(
    name="c_sdk",
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
)

dllext = "*.dll"
if platform.startswith("linux"):
    dllext = "*.so"
dllfiles = glob.iglob(os.path.join("./lib/{}/".format(platform), dllext))
for f in dllfiles:
    if os.path.isfile(f):
        shutil.copy2(f, "./{}".format(os.path.split(f)[1]))


version_info = sys.version_info

if platform == "linux-x86_64":
    system = "linux"
    ext = "so"
elif platform == "win-amd64":
    system = "win64"
    ext = "pyd"
else:
    system = "win32"
    ext = "pyd"
dyn_file = (
    f"./lib/gmpytool/py{version_info.major}{version_info.minor}/{system}/gmpytool.{ext}"
)
shutil.copy2(dyn_file, f"./{os.path.basename(dyn_file)}")
