# type: ignore
import setuptools

data_files = []

setuptools.setup(
    name="widip",
    version="0.0.1",
    author="Martin Coll",
    author_email="mcoll@dc.uba.ar",
    description="Widip is an interactive environment for computing with wiring diagrams in modern systems",
    url="https://github.com/colltoaction/widip",
    project_urls={
        "Bug Tracker": "https://github.com/colltoaction/widip/issues",
    },
    license="CC0-1.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=["widip"],
    package_data={},
    data_files=data_files,
    install_requires=["discopy>=1.1.7", "pyyaml>=6.0.1", "watchdog>=4.0.1"],
    python_requires=">=3.11",
    entry_points={'console_scripts': 'widip=:'},
)
