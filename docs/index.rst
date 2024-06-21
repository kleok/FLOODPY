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


Algorithms implemented in the software are described in detail at our publication. If FLOODPY was useful for you, we encourage you to cite the following work.
    
Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

.. seealso::
   You can also have a look at other works that are using FLOODPY:

- Gounari 0., Falagas A., Karamvasis K., Tsironis V., Karathanassi V., Karantzalos K.: Floodwater Mapping & Extraction of Flood-Affected Agricultural Fields. Living Planet Symposium Bonn 23-27 May 2022. https://drive.google.com/file/d/1HiGkep3wx45gAQT6Kq34CdECMpQc8GUV/view?usp=sharing

- Zotou I., Karamvasis K., Karathanassi V., Tsihrintzis V.: Sensitivity of a coupled 1D/2D model in input parameter variation exploiting Sentinel-1-derived flood map. 7th IAHR Europe Congress. September 7-9, 2022. Page 247 at https://www.iahreuropecongress.org/PDF/IAHR2022_ABSTRACT_BOOK.pdf

- Zotou I, Karamvasis K, Karathanassi V, Tsihrintzis VA. Potential of Two SAR-Based Flood Mapping Approaches in Supporting an Integrated 1D/2D HEC-RAS Model. Water. 2022; 14(24):4020. https://doi.org/10.3390/w14244020 


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
