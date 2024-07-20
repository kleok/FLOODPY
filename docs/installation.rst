Installation
============

.. important::
    The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.9, SNAP 9.0

Steps
-----

1. Install snap gpt including Sentinel-1 toolbox.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can download SNAP manually from `here <https://step.esa.int/main/download/snap-download/>`_ and install it using the following commands:

.. code-block:: bash

	chmod +x install_snap.sh
	./install_snap.sh


2. Account setup for downloading Sentinel-1 acquisitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Even though we offer credentials (for demonstration reasons), we encourage you to create your own account in order to not encounter any problems due to traffic.

- Please create an account at: `Copernicus-DataSpace <https://dataspace.copernicus.eu/>`_.


3. Account setup for downloading global atmospheric model data
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

4. Download FLOODPY
^^^^^^^^^^^^^^^^^^^^^^^^^

You can download FLOODPY toolbox using the following command: 

.. code-block:: bash

	git clone https://github.com/kleok/FLOODPY.git

5. Create python environment for FLOODPY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FLOODPY is written in Python3 and relies on several Python modules. You can install them by using conda.

Create a new conda environment with required packages using the the file `FLOODPY_env.yml <https://github.com/kleok/FLOODPY/blob/main/FLOODPY_env.yml>`_.
Then you can run the following command:

.. code-block:: bash

	conda env create -f path_to_FLOODPY/FLOODPY_env.yml


6. Set environmental variables (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append to :file:`.bashrc` file:

.. code-block:: bash

	export FLOODPY_HOME= path_of_the_FLOODPY_folder
	export PYTHONPATH=${PYTHONPATH}:${FLOODPY_HOME}
	export PATH=${PATH}:${FLOODPY_HOME}/floodpy
