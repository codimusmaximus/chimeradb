from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sqlite-kg",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="SQLite Knowledge Graph with Vector Embeddings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sqlite-kg",
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
    ],
    extras_require={
        "embeddings": [
            "sentence-transformers>=2.0.0",
            "openai>=1.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
        ],
    },
    package_data={
        "sqlite_kg": ["extensions/*.dylib", "extensions/*.so"],
    },
    include_package_data=True,
)
