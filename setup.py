from setuptools import setup, find_packages

setup(
    name='tradecli',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=['tradecli'],
    install_requires=[
        'click',
        'pyyaml',
        'python-dotenv',
    ],
    entry_points='''
        [console_scripts]
        tradecli=tradecli:cli
    ''',
)
