from setuptools import setup, find_packages

setup(
    name="lilvali",
    version="0.1.0",
    description="Tiny validation library for Python",
    long_description="",
    author="Grayson Miller",
    author_email="grayson.miller124@gmail.com",
    url="",
    packages=find_packages(),
    install_requires=[],
    extras_require={"dev": ["black", "isort", "flake8", "mypy"]},
    python_requires=">=3.8",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
)
