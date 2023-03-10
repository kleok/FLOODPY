import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name = "floodpy",
    version = "0.6.0",
    author = "Kleanthis Karamvasis, Alekos Falagas",
    author_email = "karamvasis_k@hotmail.com, alek.falagas@gmail.com",
    description = "The FLOOD  PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOMPY's floodwater maps.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url="https://github.com/kleok/FLOODPY",
    packages = setuptools.find_packages(),
    license="GNU General Public License v3 or later (GPLv3+)",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.9',
    install_requires=[required],
)
