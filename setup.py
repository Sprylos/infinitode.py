import setuptools


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
    version='1.0.0',
    packages=['infinitode'],
    package_data={'infinitode': ['py.typed']},
    license='MIT',
    install_requires=['aiohttp', 'lxml', 'bs4'],
    include_package_data=True,
)
