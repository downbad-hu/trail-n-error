import sys
import os
from setuptools import setup, find_packages

setup(
    name="PyDownloadManager",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
        "pyinstaller>=4.5.0",
    ],
    entry_points={
        'console_scripts': [
            'pydownloadmanager=main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A multi-threaded download manager with browser integration",
    keywords="download, manager, browser, integration",
    python_requires=">=3.6",
)