"""
Setup configuration for customs-kb package.
"""
from setuptools import setup, find_packages

setup(
    name="customs-kb",
    version="0.1.0",
    description="US Customs Knowledge Base POC",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.7",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "qdrant-client>=1.7.0",
        "sentence-transformers>=2.3.1",
        "httpx>=0.26.0",
        "pandas>=2.1.4",
        "beautifulsoup4>=4.12.3",
        "lxml>=5.1.0",
        "tenacity>=8.2.3",
        "tqdm>=4.66.1",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "ipython>=8.20.0",
            "jupyter>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "customs-kb=src.cli.main:cli",
        ],
    },
)
