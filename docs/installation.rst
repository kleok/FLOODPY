Installation
============

.. important::
    The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

Steps
-----

1. Install snap gpt including `Sentinel-1 toolbox <https://step.esa.int/main/download/snap-download/previous-versions/>`_.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the installation of ESA SNAP you can run the automated script `aux/install_snap.sh <https://github.com/kleok/FLOMPY/blob/main/aux/install_snap.sh>`_ for downloading and installing the official Linux installer from the official ESA repository. To install SNAP run the following commands:

.. code-block:: bash

	chmod +x install_snap.sh
	./install_snap.sh

2. Account setup for downloading Sentinel-1 acquisitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sentinel-1 data download functionality require user credentials. More information at `scihub <https://scihub.copernicus.eu/>`_.

3. Account setup for downloading global atmospheric model data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS). You have to create a new account on the CDS website if you don't own a user account yet. After the creation of your profile, you will find your user id (UID) and your personal API Key. Now, a :file:`.cdsapirc` file must be created under your :file:`HOME`  directory with the following information:

.. code-block::

	url: https://cds.climate.copernicus.eu/api/v2
	key: UID:personal API Key

In case you dont want to create the :file:`.cdsapirc`  file manually, you can run `aux/install_CDS_key.sh <https://github.com/kleok/FLOMPY/blob/main/aux/install_CDS_key.sh>`_ script as follows:

.. code-block:: bash

	chmod +x install_CDS_key.sh
	./install_CDS_key.sh

More details on CDSAPI can be found `here <https://cds.climate.copernicus.eu/api-how-to>`_.

4. Download FLOMPY
^^^^^^^^^^^^^^^^^^^^^^^^^

First you have to download Flompy toolbox using the following command

.. code-block:: bash

	git clone https://github.com/kleok/FLOMPY.git

5. Create python environment for FLOMPY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FLOMPY is written in Python3 and relies on several Python modules. You can install them by using conda or pip.

- Using **conda**
Create a new conda environement with required packages using the the file `FLOMPY_env.yml <https://github.com/kleok/FLOMPY/blob/main/FLOMPY_env.yml>`_.

.. code-block:: bash

	conda env create -f ~/FLOMPY/FLOMPY_env.yml

- Using **pip**
You can install python packages using `setup.py <https://github.com/kleok/FLOMPY/blob/main/setup.py>`_.

.. code-block:: bash

	cd ~/FLOMPY
	pip install .

6. Set environmental variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
On GNU/Linux, append to :file:`.bashrc` file:

.. code-block:: bash

    export FLOMPY_HOME=~/FLOMPY
    export PYTHONPATH=${PYTHONPATH}:${FLOMPY_HOME}
    export PATH=${PATH}:${FLOMPY_HOME}
