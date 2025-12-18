from setuptools import setup, find_packages

setup(
    name="mygreetcli",
    version="0.1",
    py_modules=["cli"],  # or your package name if it's more than one module
    install_requires=[
        "click",  # only include this if you are using click
    ],
    entry_points={
        'console_scripts': [
            'tradecli = cli:main',  # For argparse, or use 'greetcli = greet:greet' for click
        ],
    },
)
