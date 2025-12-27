from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="finance-tracker",
    version="0.1.0",
    author="Your Name",
    description="AI-powered personal finance tracker CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "anthropic>=0.40.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "python-dateutil>=2.8.0",
        "pyyaml>=6.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.0.280",
        ]
    },
    entry_points={
        "console_scripts": [
            "finance=src.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
