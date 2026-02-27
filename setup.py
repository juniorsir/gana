from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="gana-player",
    version="1.0.6",
    description="A Cyberpunk CLI Music Player for Hackers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="JuniorSir",
    author_email="juniorsir011@gmail.com",
    url="https://github.com/juniorsir/gana", # Link to your GitHub
    packages=find_packages(),
    install_requires=[
        "yt-dlp>=2023.10",
        "requests",
        # We don't list mpv here because it's a system binary, not a python package
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Android", # For Termux
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "gana=gana.cli:main",
            "gana-player=gana.cli:main",
        ],
    },
    python_requires=">=3.8",
)
