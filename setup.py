from setuptools import setup, find_packages

setup(
    name='trade_journal',
    version='0.1',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'pandas',
        'scipy',
        'matplotlib',
        'statemachine',
        # Add other dependencies here
    ],
    entry_points={
        'console_scripts': [
            # Define any command-line scripts here
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A package for managing trade journals.',
    url='https://github.com/yourusername/trade_journal',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
) 