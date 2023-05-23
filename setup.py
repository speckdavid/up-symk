#!/usr/bin/env python3
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
import os
import shutil

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            python, abi, plat = _bdist_wheel.get_tag(self)
            # We don't link with python ABI, but require python3
            python, abi = 'py3', 'none'
            return python, abi, plat
except ImportError:
    bdist_wheel = None


SYMK_REPO = 'https://github.com/speckdavid/symk.git'
# SYMK_RELEASE = 'release-22.12'
SYMK_RELEASE = None
# CHANGESET is ignored if release is not None
SYMK_CHANGESET = 'abb9ce701bfd55f675e242bf95fe50f0eea5fefe'


def clone_and_compile_symk():
    curr_dir = os.getcwd()
    print("Cloning SymK repository...")
    if SYMK_RELEASE is not None:
        subprocess.run(['git', 'clone', '-b', SYMK_RELEASE, SYMK_REPO])
    else:
        subprocess.run(['git', 'clone', SYMK_REPO])

    shutil.move('symk', 'up_symk/symk')
    os.chdir('up_symk/symk')
    if SYMK_RELEASE is None:
        subprocess.run(['git', 'checkout', SYMK_CHANGESET])
    print("Building SymK (this can take some time)...")
    build = subprocess.run(['./build.py'])
    strip_downward = subprocess.run(
        ['strip', '--strip-all', 'builds/release/bin/downward'])
    strip_preprocess = subprocess.run(
        ['strip', '--strip-all', 'builds/release/bin/preprocess'])
    os.chdir(curr_dir)


class install_symk(build_py):
    """Custom install command."""

    def run(self):
        clone_and_compile_symk()
        build_py.run(self)


class install_symk_develop(develop):
    """Custom install command."""

    def run(self):
        clone_and_compile_symk()
        develop.run(self)


long_description = "This package makes the [SymK](https://github.com/speckdavid/symk) planner available in the [unified_planning library](https://github.com/aiplan4eu/unified-planning) by the [AIPlan4EU project](https://www.aiplan4eu-project.eu/)."

setup(name='up_symk',
      version='0.0.2',
      description='Unified Planning Integration of the SymK planner',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='David Speck',
      author_email='david.speck@liu.se',
      url='https://github.com/aiplan4eu/symk/',
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence',
                   ],
      packages=['up_symk'],
      package_data={
          "": ['fast_downward.py',
               'symk/fast-downward.py',
               'symk/README.md',
               'symk/LICENSE.md',
               'symk/builds/release/bin/*',
               'symk/builds/release/bin/translate/*',
               'symk/builds/release/bin/translate/pddl/*',
               'symk/builds/release/bin/translate/pddl_parser/*',
               'symk/driver/*',
               'symk/driver/portfolios/*'
               ]
      },
      cmdclass={
          'bdist_wheel': bdist_wheel,
          'build_py': install_symk,
          'develop': install_symk,
      },
      has_ext_modules=lambda: True
      )
