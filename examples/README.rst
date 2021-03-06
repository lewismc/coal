=============
COAL Examples
=============

Welcome to the COAL examples directory. Here you will find helpful example scripts enabling you to run and experiment with all COAL functionality. The example here are based entirely off of the `usage <https://capstone-coal.github.io/docs#usage>`__ scenarios provided over at the main COAL Website.

Please report any issues you find here over at the `pycoal issue tracker <https://github.com/capstone-coal/pycoal/issues>`__ `labeling <https://github.com/capstone-coal/pycoal/labels>`__ your issue appropriately using **examples** and then the type of issue you are having e.g. **help wanted**, **question**, etc.

Prerequisites
-------------

Build and Test pycoal
^^^^^^^^^^^^^^^^^^^^^
Please `build the pycoal source <https://github.com/capstone-coal/pycoal/#source>`__ and then `test <https://github.com/capstone-coal/pycoal/#tests>`__ it. 

AVIRIS-NG Data
^^^^^^^^^^^^^^
pycoal does not come packaged with absolutely everything e.g. spectral library(ies), input hyperspectral spectroscopy data, etc. In order to run the following examples, you need to download AVIRIS data to the **examples** directory. N.B. This data may take a significant amount of time to download depending on your network... go and make yourself a cup of tea or two!

::

	wget -m "ftp://avng.jpl.nasa.gov/AVNG_2015_data_distribution/L2/ang20150420t182050_rfl_v1e/"

A full description of what this data actually is, is detailed in the `AVIRIS-NG Distribution Document <ftp://avng.jpl.nasa.gov/AVNG_2015_data_distribution/L2/ang20150420t182050_rfl_v1e/ang20150420t182050_v1e_README.txt>`__.

USGS Digital Spectral Library splib06a and splib07a
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you navigate to *pycoal/tests/* you will see two files named **s06av95a_envi.hdr** and *s06av95a_envi.sli*. These files, as explained in the example code, are the `USGS Digital Spectral Library splib06a <https://speclab.cr.usgs.gov/spectral.lib06/ds231/index.html>`__ header and digital spectral index files respectively. In *pycoal/tests/* you will also see two files named **s07_AV95_envi.hdr** and *s07_AV95_envi.sli* for `USGS Spectral Library Version 7 <https://speclab.cr.usgs.gov/spectral-lib.html>`__. Please DO NOT move these files as they are read in a relative fashion.

USGS National Hydrography Dataset (NHD) Best Resolution for New Mexico State or Territory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The `National Hydrography Dataset <https://nhd.usgs.gov/NHD_High_Resolution.html>`__ (NHD), a component of `The National Map <https://nationalmap.gov/>`__, represents the water drainage network of the United States with features such as rivers, streams, canals, lakes, ponds, coastline, dams, and streamgages. The NHD is the surface water component on the `US Topo <https://nationalmap.gov/ustopo/index.html>`__ map product produced by the USGS. These data, in digital vector geographic information system (GIS) format, are designed to be used in general mapping and in the analysis of surface water systems. For this example we are using the Best Resolution data for New Mexico State or Territory, it can be obtained as follows

::

	wget -m "ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/Hydrography/NHD/State/HighResolution/Shape/NHD_H_New_Mexico_Shape.zip" && unzip rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/Hydrography/NHD/State/HighResolution/Shape/NHD_H_New_Mexico_Shape.zip

Modifying Constants - Using a Different Hyperspectral Image, Hydrography Dataset, or Spectral Version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The constants.py file in this directory provides constants shared by all
examples. It is recommended to use this file when changing the image that is
classified because changing it once in constants.py will allow mineral,
mining, and environment algorithms to all use the same file name.
Additionally, you can switch between using Spectral Library version 6 or 7
in constants.py, as well as setting the option to only classify a subset of
an image (see comments in constants.py for more info).


Mineral Classification
----------------------
The `Mineral Classification API <http://pycoal.readthedocs.io/en/latest/mineral.html>`__ provides methods for generating visible-light and mineral classified images. Mineral classification can take hours to days depending on the size of the spectral library and the available computing resources, so running a script in the background is recommended.

**N.B.** To generate a Hypercube for any given scene, you need to run something similar to the following

:: 

  ipython --pylab=WX
  
  from pycoal import mineral
  
  mineral_classification = mineral.MineralClassification(library_file_name="../pycoal/tests/s07_AV95_envi.hdr", scores_file_name="../pycoal/tests/images/ang20140912t192359_corr_v1c_img_2580-2590_540-550.hdr_scores.hdr", subset_rows=None, subset_cols=None)

  mineral_classification.to_hypercube("/Users/lmcgibbn/Downloads/pycoal/pycoal/tests/images/ang20140912t192359_corr_v1c_img_2580-2590_540-550.hdr")

You will then be able to view an interactive hypercube.


Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^

::

	usage: example_mineral.py [-h] [-i INPUT] [-l SLIB]

	example_mineral -- an example script which demonstrates COAL mineral classification

	VERSION 0.5.2

	Copyright (C) 2017-2019 COAL Developers

	This program is free software; you can redistribute it and/or 
	modify it under the terms of the GNU General Public License 
	as published by the Free Software Foundation; version 2.

	This program is distributed in the hope that it will be useful, 
	but WITHOUT ANY WARRANTY; without even the implied warranty 
	of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
	See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public 
	License along with this program; if not, write to the Free 
	Software Foundation, Inc., 51 Franklin Street, Fifth 
	Floor, Boston, MA 02110-1301, USA.

	USAGE

	optional arguments:
		-h, --help            	show this help message and exit
		-i INPUT, --input INPUT
                        		Input file to be processed [default:
                        		ang20150420t182050_corr_v1e_img.hdr
		-l SLIB, --slib SLIB  	Spectral Library filename [default: s06av95a_envi.hdr]

After running this Python script, you will see two new images written locally, namely

 * **ang20150420t182050_corr_v1e_img_rgb.hdr** - a visible-light image, and
 * **ang20150420t182050_corr_v1e_img_class.hdr** - a mineral classified image

Mining Classification
---------------------
The `Mining Identification API <http://pycoal.readthedocs.io/en/latest/mining.html>`__ filters mineral classified images to identify specific classes of interest, by default proxies for coal mining in the USGS Digital Spectral Library 06 or 07.

Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^

::

	usage: example_mining.py [-h] [-mi INPUT] [-mo OUTPUT] [-v SPECTRAL_VERSION]

	example_mining -- an example script which demonstrates COAL mining classification

  	VERSION 0.5.2

  	Copyright (C) 2017-2019 COAL Developers

  	This program is free software; you can redistribute it and/or
  	modify it under the terms of the GNU General Public License
  	as published by the Free Software Foundation; version 2.

  	This program is distributed in the hope that it will be useful,
  	but WITHOUT ANY WARRANTY; without even the implied warranty
  	of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  	See the GNU General Public License for more details.

  	You should have received a copy of the GNU General Public
  	License along with this program; if not, write to the Free
  	Software Foundation, Inc., 51 Franklin Street, Fifth
  	Floor, Boston, MA 02110-1301, USA.

	USAGE

	optional arguments:
  		-h, --help            show this help message and exit
  		-mi INPUT, --mineral_input INPUT
                        Input classified mineral file to be processed
                        [default: ang20150420t182050_corr_v1e_img_class.hdr]
  		-mo OUTPUT, --mining_output OUTPUT
                        Output mining classified image filename [default:
                        ang20150420t182050_corr_v1e_img_class_mining.hdr]
		-v SPECTRAL_VERSION, --spectral_version SPECTRAL_VERSION
			USGS Spectral Library Version Number (6 or 7) 
			[default: 6]


Environment Classification
--------------------------
The `Environmental Correlation API <https://pycoal.readthedocs.io/en/latest/environment.html>`__ finds pixels in a mining classified image that are within a certain number of meters from features in a vector layer such as flow lines in the `National Hydrography Dataset <https://nhd.usgs.gov/NHD_High_Resolution.html>`__ (NHD).

Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^

::

	usage: example_environment.py [-h] [-m MINING_FILENAME] [-hy VECTOR_FILENAME]
                              [-e CORRELATION_FILENAME]

	example_environment -- an example script which demonstrates COAL environmental classification

  	VERSION 0.5.2

  	Copyright (C) 2017-2019 COAL Developers

  	This program is free software; you can redistribute it and/or
  	modify it under the terms of the GNU General Public License
  	as published by the Free Software Foundation; version 2.

  	This program is distributed in the hope that it will be useful,
  	but WITHOUT ANY WARRANTY; without even the implied warranty
  	of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  	See the GNU General Public License for more details.

  	You should have received a copy of the GNU General Public
  	License along with this program; if not, write to the Free
  	Software Foundation, Inc., 51 Franklin Street, Fifth
  	Floor, Boston, MA 02110-1301, USA.

	USAGE

	optional arguments:
  		-h, --help      show this help message and exit
  		-m MINING_FILENAME, --mining MINING_FILENAME
                        Input mining classified file to be processed [default:
                        ang20150420t182050_corr_v1e_img_class_mining.hdr]
  		-hy VECTOR_FILENAME, --hydrography VECTOR_FILENAME
                        Path to hydrography data [default:
                        Shape/NHDFlowline.shp]
  		-e CORRELATION_FILENAME, --environment CORRELATION_FILENAME
                        Output environmental correlation image [default: ang20
                        150420t182050_corr_v1e_img_class_mining_NHDFlowline_co
                        rrelation.hdr]
