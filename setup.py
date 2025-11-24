from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chimeradb",
    version="0.1.1",
    author="Alexander Leirvåg",
    author_email="alexander@prismeta.com",
    description="Knowledge graph + vector search + SQL analytics in SQLite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codimusmaximus/chimeradb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
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
    package_data={
        "chimeradb": ["extensions/*.dylib", "extensions/*.so"],
    },
    include_package_data=True,
)
