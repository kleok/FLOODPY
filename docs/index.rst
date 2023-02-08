.. FLOODPY documentation master file, created by
   sphinx-quickstart on Sat Dec  4 13:58:33 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to FLOODPY's documentation!
===================================

What is FLOODPY?
----------------

The FLOOD PYthon toolbox (FLOODPY) is a free and open-source python toolbox for mapping of floodwater.

.. image:: ../figures/pinieios_results_github.png
  :width: 800

How does it work?
-----------------

The FLOod Mapping PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOODPY's floodwater maps.

.. seealso::
    Algorithms implemented in the software are described in detail at our publication. If FLOODPY was useful for you, we encourage you to cite the following work.
    
- Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

Contact us
----------
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recommendations.
Any help is very welcome!


.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Contents:
   
   quickstart
   installation
   modules
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
