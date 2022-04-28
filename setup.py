import setuptools
import re

version = ''
with open('infinitode/__init__.py') as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)  # type: ignore

readme = ''
with open('README.md') as f:
    readme = f.read()

setuptools.setup(
    name='infinitode.py',
    author='Sprylos',
    url='https://github.com/Sprylos/infinitode.py',
    description='A python wrapper for the Infinitode 2 API.',
    long_description=readme,
    long_description_content_type='text/markdown',
    version=version,
    packages=['infinitode'],
    package_data={'infinitode': ['py.typed']},
    license='MIT',
    install_requires=['aiohttp', 'lxml', 'bs4'],
    include_package_data=True,
)
