Installation
============

.. important::
    The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.9, SNAP 9.0
	For windows we the installation notes can be found `here <https://github.com/kleok/FLOODPY/blob/main/aux/installation_notes_win.pdf>`_.

Steps
-----

1. Install snap gpt including Sentinel-1 toolbox.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Option 1: You can either run the automated script `aux/install_snap.sh <https://github.com/kleok/FLOODPY/blob/main/aux/install_snap.sh>`_ for downloading and installing the official Linux installer from the official ESA repository.

- Option 2: You can download SNAP manually from here and install it using the following commands:

.. code-block:: bash

	chmod +x install_snap.sh
	./install_snap.sh


2. Install aria for downloading Sentinel-1 acquisitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Please also install aria using the following command:

.. code-block:: bash

	sudo apt-get install aria2

3. Account setup for downloading Sentinel-1 acquisitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Even though we offer credentials (for demonstration reasons), we encourage you to create your own account in order to not encounter any problems due to traffic.

- Please create an account at: `ESA-scihub <https://scihub.copernicus.eu/dhus/#/self-registration>`_.

- Please create an account at: `NASA-earthdata <https://urs.earthdata.nasa.gov/users/new>`_.


4. Account setup for downloading global atmospheric model data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, FloodPy is based on ERA-5 data. ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS). You have to create a new account `here <https://cds.climate.copernicus.eu/user/register>`_ if you don't own a user account yet. After the creation of your profile, you will find your user id (UID) and your personal API Key on your User profile page.


ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS). You have to create a new account on the CDS website if you don't own a user account yet. After the creation of your profile, you will find your user id (UID) and your personal API Key. Now, a :file:`.cdsapirc` file must be created under your :file:`HOME`  directory with the following information:


- Option 1: create manually a .cdsapirc file under your HOME directory with the following information:

.. code-block:: bash

	url: https://cds.climate.copernicus.eu/api/v2
	key: UID:personal API Key

- Option 2: Run aux/install_CDS_key.sh script as follows:

.. code-block:: bash

	chmod +x install_CDS_key.sh
	./install_CDS_key.sh

More details on CDSAPI can be found `here <https://cds.climate.copernicus.eu/api-how-to>`_.

5. Download FLOODPY
^^^^^^^^^^^^^^^^^^^^^^^^^

We suggest you to download FLOODPY toolbox using the following command: 

.. code-block:: bash

	git clone https://github.com/kleok/FLOODPY.git

6. Create python environment for FLOODPY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FLOODPY is written in Python3 and relies on several Python modules. You can install them by using conda or pip.

- Using **conda**

Create a new conda environement with required packages using the the file `FLOODPY_env.yml <https://github.com/kleok/FLOODPY/blob/main/FLOODPY_env.yml>`_.
In case you downloaded FLOODPY in your home directory you can run the following command:

.. code-block:: bash

	conda env create -f ~/FLOODPY/FLOODPY_env.yml

- Using **pip**
You can install python packages using `setup.py <https://github.com/kleok/FLOODPY/blob/main/setup.py>`_.
In case you downloaded FLOODPY in your home directory you can run the following command:

.. code-block:: bash

	cd ~/FLOODPY
	pip install .

7. Set environmental variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append to :file:`.bashrc` file:

.. code-block:: bash

	export FLOODPY_HOME= path_of_the_FLOODPY_folder
	export PYTHONPATH=${PYTHONPATH}:${FLOODPY_HOME}
	export PATH=${PATH}:${FLOODPY_HOME}/floodpy
