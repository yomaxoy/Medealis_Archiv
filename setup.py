from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="medealis-archiv",
    version="1.0.0",
    author="Medealis GmbH",
    author_email="info@medealis.de",
    description="Verwaltungssystem für medizinische Geräte-Lieferungen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/medealis/medealis-archiv",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "medealis-archiv=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.docx"],
    },
)