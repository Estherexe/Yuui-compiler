"""
Setup da Yuui-Lang
Execute: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name='yuui-lang',
    version='0.2.0',
    description='Linguagem de Programacao para Sistemas Operacionais',
    author='Yuui',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
)
