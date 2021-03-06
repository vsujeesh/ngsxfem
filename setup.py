#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import platform
import subprocess
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)
class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))
        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")
        for ext in self.extensions:
            self.build_extension(ext)
    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        # required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable,
                      '-DCMAKE_CXX_COMPILER=ngscxx',
                      '-DCMAKE_LINKER=ngsld',
                      '-DBUILD_STUB_FILES=ON',
                      '-DBUILD_NGSOLVE=OFF']
        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]
        if platform.system() == "Windows":
            #not expected to work... (but who knows..)
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']
        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)
        
        subprocess.check_call(['mv', 'ngsxfem_py.so', 'xfem'], cwd=self.build_lib)

setup(
    name='xfem',
    version='1.3.2008dev1',
    author='Christoph Lehrenfeld',
    author_email='lehrenfeld@math.uni-goettingen.de',
    description='(ngs)xfem is an Add-on library to Netgen/NGSolve for unfitted/cut FEM.',
    long_description='(ngs)xfem is an Add-on library to Netgen/NGSolve which enables the use of unfitted finite element technologies known as XFEM, CutFEM, TraceFEM, Finite Cell, ... . ngsxfem is an academic software. Its primary intention is to facilitate the development and validation of new numerical methods.',
    url="https://github.com/ngsxfem/ngsxfem",
    ext_modules=[CMakeExtension('ngsxfem_py')],
    cmdclass=dict(build_ext=CMakeBuild),
    packages=["xfem"], 
    package_dir={"xfem" : "python",
                 "xfem.cutmg" : "python",
                 "xfem.lsetcurv" : "lsetcurving",
                 "xfem.lset_spacetime" : "spacetime",
                 "xfem.mlset" : "python",
                 "xfem.utils" : "utils"},
    python_requires='>=3.5',
)
