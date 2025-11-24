from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chimeradb",
    version="0.2.23",
    author="Alexander Leirvåg",
    author_email="alexander@prismeta.com",
    description="Knowledge graph + vector search + SQL analytics powered by DuckDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codimusmaximus/chimeradb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "duckdb>=1.1.3,<1.2.0",  # Pin to 1.1.x for duckpgq compatibility
        "numpy>=1.20.0",
        "sentence-transformers>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
        ],
    },
    include_package_data=True,
)
