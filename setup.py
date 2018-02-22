import sys

from setuptools import setup, find_packages

with open('version.py') as inp:
    exec(inp.read())
__version__ = STR

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

script_name = 'distxargs'

setup(
    name='distxargs',
    version=__version__,
    install_requires=requirements,
    author='Toshihiro Kamiya',
    author_email='kamiya@mbj.nifty.com',
    entry_points="""
      [console_scripts]
      %s = distxargs:main
      """ % script_name,
    packages=find_packages(),
    license='License :: OSI Approved :: BSD License',
    description='Parallel execution with a pool of worker processes on cluster via ssh.',
)
