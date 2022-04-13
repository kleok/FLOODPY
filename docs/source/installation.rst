Installation
============

FLOMPY is written in Python3 and relies on several Python modules. We recommend using `conda` to install
the python environment and the prerequisite packages, because of the convenient management.

.. important::
    The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

Steps
-----

1.1 Create python environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a python environment using the :file:`requirements.txt` file.

1.2 Install SNAP gpt
^^^^^^^^^^^^^^^^^^^^

Install SNAP gpt including `Sentinel-1 toolbox <https://step.esa.int/main/download/snap-download/>`_.

1.3 Setup an account for downloading Sentinel-1 data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sentinel-1 data download functionality requires an active `scihub.copernicus.eu <https://scihub.copernicus.eu/>`_ user account.

1.4 Setup an account for downloading ERA-5 data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS), create a new account on the CDS website if you don't own a user account yet. On the profile, you will find your user id (UID) and your personal API Key. Create a file :file:`.cdsapirc` under your home directory and add the following information:

.. code-block::

   url: https://cds.climate.copernicus.eu/api/v2
   key: UID:personal API Key

CDS API is needed to auto-download ERA5 ECMWF data: conda install -c conda-forge cdsapi
More details on CDSAPI can be found [here](https://cds.climate.copernicus.eu/api-how-to).

.. seealso::
    More details on CDS API can be found `here <https://cds.climate.copernicus.eu/api-how-to>`_.

1.5 Download FLOMPY
^^^^^^^^^^^^^^^^^^^

Clone FLOMPY:

.. code-block:: bash

    git clone https://github.com/kleok/FLOMPY.git

On GNU/Linux, append to :file:`.bashrc` file:

.. code-block:: bash

    export FLOMPY_HOME=~/FLOMPY
    export PYTHONPATH=${PYTHONPATH}:${FLOMPY_HOME}
    export PATH=${PATH}:${FLOMPY_HOME}
