from setuptools import setup, find_packages

setup(
    name="arrestx",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml",
        "pandas",
        "pymongo",
        "requests",
        "gradio",
        "pypdf",
        "pytesseract",
    ],
    entry_points={
        "console_scripts": [
            "arrestx=arrestx.cli:main",
        ],
    },
)