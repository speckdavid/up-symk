from setuptools.command.build_py import build_py as _build_py
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
import os
import shutil
import subprocess

def clone_and_compile_symk():
    SYMK_REPO = 'https://github.com/speckdavid/symk.git'
    SYMK_CHANGESET = '1f54c5eb72cc9328603722cc07b478d33d408a94'
    
    curr_dir = os.getcwd()
    print("Cloning SymK repository...")
    subprocess.run(['git', 'clone', SYMK_REPO])

    shutil.move('symk', 'up_symk/symk')
    os.chdir('up_symk/symk')
    subprocess.run(['git', 'checkout', SYMK_CHANGESET])
    print("Building SymK (this can take some time)...")
    build = subprocess.run(['python', 'build.py', 'release'],
                           universal_newlines = True)
    os.chdir(curr_dir)

class install_symk(_build_py):
    """Custom install command."""

    def run(self, *args, **kwargs):
        clone_and_compile_symk()
        super().run(*args, **kwargs)
    

class bdist_wheel(_bdist_wheel):

    def finalize_options(self):
        super().finalize_options()
        # Mark us as not a pure python package
        self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = super().get_tag()
        # We don't link with python ABI, but require python3
        python, abi = 'py3', 'none'
        return python, abi, plat