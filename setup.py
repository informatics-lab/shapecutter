import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="shapecutter",
    version="0.0.1",
    author="Peter Killick",
    author_email="peter.killick@informaticslab.co.uk",
    description="Cut data out of raster arrays around shapely geometries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/informatics-lab/shapecutter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "geopandas>=0.9.0",
        "scitools-iris>=2.4.0",
        "Shapely>=1.7.0"
    ]
)