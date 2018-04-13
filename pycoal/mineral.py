# Copyright (C) 2017-2018 COAL Developers
#
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation; version 2.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty 
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public 
# License along with this program; if not, write to the Free 
# Software Foundation, Inc., 51 Franklin Street, Fifth 
# Floor, Boston, MA 02110-1301, USA.

import sys
import os
import inspect
import logging
import math
import numpy
import pycoal
import spectral
import time
import importlib
from sys import path
sys.path.insert(0, '../pycoal')
importlib.reload(sys)
import fnmatch
import mineral
import shutil
import mmap

class MineralClassification:

    def __init__(self, library_file_name, class_names=None, threshold=0.0, in_memory=False):
        """
        Construct a new ``MineralClassification`` object with a spectral library
        in ENVI format such as the `USGS Digital Spectral Library 06
        <https://speclab.cr.usgs.gov/spectral.lib06/>`_ or the `ASTER Spectral
        Library Version 2.0 <https://asterweb.jpl.nasa.gov/>`_ converted with
        ``pycoal.mineral.AsterConversion.convert()``.

        If provided, the optional class name parameter will initialize the
        classifier with a subset of the spectral library, otherwise the full
        spectral library will be used.

        The optional threshold parameter defines a confidence value between zero
        and one below which classifications will be discarded, otherwise all
        classifications will be included.

        In order to improve performance on systems with sufficient memory,
        enable the optional parameter to load entire images.

        Args:
            library_file_name (str):        filename of the spectral library
            class_names (str[], optional): list of names of classes to include
            threshold (float, optional):  classification threshold
            in_memory (boolean, optional): enable loading entire image
        """
        # load and optionally subset the spectral library
        self.library = spectral.open_image(library_file_name)
        if class_names is not None:
            self.library = self.subset_spectral_library(self.library, class_names)

        # store the threshold
        self.threshold = threshold

        # store the memory setting
        self.in_memory = in_memory
        logging.info("Instantiated Mineral Classifier with following specification: " \
         "-spectral library '%s', -class names '%s', -threshold '%s', -in_memory '%s'" 
            %(library_file_name, class_names, threshold, in_memory))

    def classify_image(self, image_file_name, classified_file_name):
        """
        Classify minerals in an AVIRIS image using spectral angle mapper
        classification and save the results to a file.

        Args:
            image_file_name (str):      filename of the image to be classified
            classified_file_name (str): filename of the classified image

        Returns:
            None
        """
        start = time.time()
        logging.info("Starting Mineral Classification for image '%s', saving classified image to '%s'" 
            %(image_file_name, classified_file_name))
        # open the image
        image = spectral.open_image(image_file_name)
        if self.in_memory:
            data = image.load()
        else:
            data = image.asarray()
        M = image.shape[0]
        N = image.shape[1]

        # define a resampler
        # TODO detect and scale units
        # TODO band resampler should do this
        resample = spectral.BandResampler([x/1000 for x in image.bands.centers],
                                          self.library.bands.centers)

        # allocate a zero-initialized MxN array for the classified image
        classified = numpy.zeros(shape=(M,N), dtype=numpy.uint16)

        # for each pixel in the image
        for x in range(M):

            for y in range(N):

                # read the pixel from the file
                pixel = data[x,y]

                # if it is not a no data pixel
                if not numpy.isclose(pixel[0], -0.005) and not pixel[0]==-50:

                    # resample the pixel ignoring NaNs from target bands that don't overlap
                    # TODO fix spectral library so that bands are in order
                    resampled_pixel = numpy.nan_to_num(resample(pixel))

                    # calculate spectral angles
                    angles = spectral.spectral_angles(resampled_pixel[numpy.newaxis,
                                                                     numpy.newaxis,
                                                                     ...],
                                                      self.library.spectra)

                    # normalize confidence values from [pi,0] to [0,1]
                    for z in range(angles.shape[2]):
                        angles[0,0,z] = 1-angles[0,0,z]/math.pi

                    # get index of class with largest confidence value
                    index_of_max = numpy.argmax(angles)

                    # classify pixel if confidence above threshold
                    if angles[0,0,index_of_max] > self.threshold:

                        # index from one (after zero for no data)
                        classified[x,y] = index_of_max + 1

        # save the classified image to a file
        spectral.io.envi.save_classification(
            classified_file_name,
            classified,
            class_names=['No data']+self.library.names,
            metadata={
                'data ignore value': 0,
                'description': 'COAL '+pycoal.version+' mineral classified image.',
                'map info': image.metadata.get('map info')
            })

        # remove unused classes from the image
        pycoal.mineral.MineralClassification.filter_classes(classified_file_name)
        end = time.time()
        seconds_elapsed = end - start
        m, s = divmod(seconds_elapsed, 60)
        h, m = divmod(m, 60)
        logging.info("Completed Mineral Classification. Time elapsed: '%d:%02d:%02d'" % (h, m, s))

    @staticmethod
    def filter_classes(classified_file_name):
        """
        Modify a classified image to remove unused classes.

        Args:
            classified_file_name (str): file of the classified image

        Returns:
            None
        """

        # open the image
        classified = spectral.open_image(classified_file_name)
        data = classified.asarray()
        M = classified.shape[0]
        N = classified.shape[1]

        # allocate a copy for reindexed pixels
        copy = numpy.zeros(shape=(M,N), dtype=numpy.uint16)

        # find classes actually present in the image
        classes = sorted(set(classified.asarray().flatten().tolist()))
        lookup = [classes.index(i) if i in classes else 0 for i in range(int(classified.metadata.get('classes')))]

        # reindex each pixel
        for x in range(M):
            for y in range(N):
                copy[x,y] = lookup[data[x,y,0]]

        # overwrite the file
        spectral.io.envi.save_classification(
            classified_file_name,
            copy,
            force=True,
            class_names=[classified.metadata.get('class names')[i] for i in classes],
            metadata=classified.metadata)

    @staticmethod
    def to_rgb(image_file_name, rgb_image_file_name, red=680.0, green=532.5, blue=472.5):
        """
        Generate a three-band RGB image from an AVIRIS image and save it to a file.

        Args:
            image_file_name (str):     filename of the source image
            rgb_image_file_name (str):  filename of the three-band RGB image
            red (float, optional):   wavelength in nanometers of the red band
            green (float, optional): wavelength in nanometers of the green band
            blue (float, optional):  wavelength in nanometers of the blue band

        Returns:
            None
        """

        # find the index of the first element in a list greater than the value
        start = time.time()
        logging.info("Starting generation of three-band RGB image from input file: '%s' with following RGB values R: '%s', G: '%s', B: '%s'" %(image_file_name, red, green, blue))
        def index_of_greater_than(elements, value):
            for index,element in enumerate(elements):
                if element > value:
                    return index

        # open the image
        image = spectral.open_image(image_file_name)

        # load the list of wavelengths as floats
        wavelength_strings = image.metadata.get('wavelength')
        wavelength_floats = list(map(float, wavelength_strings))

        # find the index of the red, green, and blue bands
        red_index = index_of_greater_than(wavelength_floats, red)
        green_index = index_of_greater_than(wavelength_floats, green)
        blue_index = index_of_greater_than(wavelength_floats, blue)

        # read the red, green, and blue bands from the image
        red_band = image[:,:,red_index]
        green_band = image[:,:,green_index]
        blue_band = image[:,:,blue_index]

        # remove no data pixels
        for band in [red_band, green_band, blue_band]:
            for x in range(band.shape[0]):
                for y in range(band.shape[1]):
                    if numpy.isclose(band[x,y,0], -0.005) or band[x,y,0]==-50:
                        band[x,y] = 0

        # combine the red, green, and blue bands into a three-band RGB image
        rgb = numpy.concatenate([red_band,green_band,blue_band], axis=2)

        # update the metadata
        rgb_metadata = image.metadata
        rgb_metadata['description'] = 'COAL '+pycoal.version+' three-band RGB image.'
        rgb_metadata['data ignore value'] = 0
        if wavelength_strings:
            rgb_metadata['wavelength'] = [
                wavelength_strings[red_index],
                wavelength_strings[green_index],
                wavelength_strings[blue_index]]
        if image.metadata.get('correction factors'):
            rgb_metadata['correction factors'] = [
                image.metadata.get('correction factors')[red_index],
                image.metadata.get('correction factors')[green_index],
                image.metadata.get('correction factors')[blue_index]]
        if image.metadata.get('fwhm'):
            rgb_metadata['fwhm'] = [
                image.metadata.get('fwhm')[red_index],
                image.metadata.get('fwhm')[green_index],
                image.metadata.get('fwhm')[blue_index]]
        if image.metadata.get('bbl'):
            rgb_metadata['bbl'] = [
                image.metadata.get('bbl')[red_index],
                image.metadata.get('bbl')[green_index],
                image.metadata.get('bbl')[blue_index]]
        if image.metadata.get('smoothing factors'):
            rgb_metadata['smoothing factors'] = [
                image.metadata.get('smoothing factors')[red_index],
                image.metadata.get('smoothing factors')[green_index],
                image.metadata.get('smoothing factors')[blue_index]]

        # save the three-band RGB image to a file
        logging.info("Saving RGB image as '%s'" % rgb_image_file_name)
        spectral.envi.save_image(rgb_image_file_name, rgb, metadata=rgb_metadata)
        end = time.time()
        seconds_elapsed = end - start
        m, s = divmod(seconds_elapsed, 60)
        h, m = divmod(m, 60)
        logging.info("Completed RGB image generation. Time elapsed: '%d:%02d:%02d'" % (h, m, s))

    @staticmethod
    def subset_spectral_library(spectral_library, class_names):

        # adapted from https://git.io/v9ThM

        """
        Create a copy of the spectral library containing only the named classes.

        Args:
            spectral_library (SpectralLibrary): ENVI spectral library
            class_names (str[]):                list of names of classes to include

        Returns:
            SpectralLibrary: subset of ENVI spectral library
        """

        # empty array for spectra
        spectra = numpy.empty((len(class_names), len(spectral_library.bands.centers)))

        # empty list for names
        names = []

        # copy class spectra and names
        for new_index, class_name in enumerate(class_names):
            old_index = spectral_library.names.index(class_name)
            spectra[new_index] = spectral_library.spectra[old_index]
            names.append(class_name)

        # copy metadata
        metadata = {'wavelength units': spectral_library.metadata.get('wavelength units'),
                    'spectra names': names,
                    'wavelength': spectral_library.bands.centers }

        # return new spectral library
        return spectral.io.envi.SpectralLibrary(spectra, metadata, {})


class AsterConversion:

    def __init__(self):
        """
        This class provides a method for converting the `ASTER Spectral
        Library Version 2.0 <https://asterweb.jpl.nasa.gov/>`_ into ENVI format.

        Args:
            None
        """
        pass

    @classmethod
    def convert(cls, data_dir="", db_file="", hdr_file=""):
        """
        This class method generates an ENVI format spectral library file.
        ``data_dir`` is optional as long as ``db_file`` is provided. Note that
        generating an SQLite database takes upwards of 10 minutes and creating
        an ENVI format file takes up to 5 minutes. Note: This feature is still
        experimental.

        Args:
            data_dir (str, optional): path to directory containing ASCII data files
            db_file (str):            name of the SQLite file that either already exists if
                                      ``data_dir`` isn't provided, or will be generated if
                                      ``data_dir`` is provided
            hdr_file (str):           name of the ENVI spectral library to generate
                                      (without the ``.hdr`` or ``.sli`` extension)
        """
        if not hdr_file:
            raise ValueError("Must provide path for generated ENVI header file.")

        elif not db_file:
            raise ValueError("Must provide path for sqlite file.")

        if data_dir:
            spectral.AsterDatabase.create(db_file, data_dir)

        aster_database = spectral.AsterDatabase(db_file)
        spectrum_ids = [x[0] for x in aster_database.query('SELECT SampleID FROM Samples').fetchall()]
        band_min = 0.38315
        band_max = 2.5082
        band_num = 128
        band_info = spectral.BandInfo()
        band_info.centers = numpy.arange(band_min, band_max, (band_max - band_min) / band_num)
        band_info.band_unit = 'micrometer'
        library = aster_database.create_envi_spectral_library(spectrum_ids, band_info)

        library.save(hdr_file)

class SpectralToAsterConversion:
    
    def __init__(self):
        """
            This class provides a method for converting `USGS Spectral Library Version 7
            <https://speclab.cr.usgs.gov/spectral-lib.html>`_ .txt files into ASTER Spectral
            Library Version 2.0 <https://asterweb.jpl.nasa.gov/> .txt files
            
            Args:
                none
            """
        pass
    
    @classmethod
    def convert(cls, library_filename=""):
        """
            This class method converts a `USGS Spectral Library Version 7
            <https://speclab.cr.usgs.gov/spectral-lib.html>`_ .txt file into
            an `ASTER Spectral Library Version 2.0 <https://asterweb.jpl.nasa.gov/>`_ .spectrum.txt file
            ASTER Library Version 2.0 Spectral Library files are in .spectrum.txt file format
            
            Spectral Library Version 7 can be downloaded `here <https://speclab.cr.usgs.gov/spectral-lib.html>`_
            
            Args:
            library_filename (str): path to Spectral File you wish to convert
            """
        if not library_filename:
            raise ValueError("Must provide path for Spectral File.")
        
        line_count = 1
        with open(library_filename,'r') as input_file:
            for line_count, l in enumerate(input_file):
                pass
            
        input_file = open(library_filename,'r')
        #Read Name of Spectra on first line of the file
        spectra_line = input_file.readline()
        spectra_name = spectra_line[23:]
        k = 0
        #Loop through file and store all wavelength values for the given Spectra
        spectra_values_file = open('SpectraValues.txt','w')
        while(k < line_count):
            spectra_wave_length = float(input_file.readline()) * 100
            spectra_wave_length = spectra_wave_length / 1000
            spectra_wave_length = float("{0:.5f}".format(spectra_wave_length))
            spectra_y_value = spectra_wave_length * 10
            line = str(spectra_wave_length) + '  ' + str(spectra_y_value)
            spectra_values_file.write(line)
            spectra_values_file.write('\n')
            k = k+1
        #Write new file in the form of an ASTER .spectrum.txt file while using stored
        #Spectra Name and stored Spectra Wavelength values`
        input_file = open(library_filename,'w')
        input_file.write('Name:')
        input_file.write(spectra_name)
        input_file.write('Type:\n')
        input_file.write('Class:\n')
        input_file.write('Subclass:\n')
        input_file.write('Particle Size:  Unknown\n')
        input_file.write('Sample No.:  0000000000\n')
        input_file.write('Owner:\n')
        input_file.write('Wavelength Range:  ALL\n')
        input_file.write('Origin: Spectra obtained from the Noncoventional Exploitation Factors\n')
        input_file.write('Data System of the National Photographic Interpretation Center.\n')
        input_file.write('Description:  Gray and black construction asphalt.  The sample was\n')
        input_file.write('soiled and weathered, with some limestone and quartz aggregate\n')
        input_file.write('showing.\n')
        input_file.write('\n')
        input_file.write('\n')
        input_file.write('\n')
        input_file.write('Measurement:  Unknown\n')
        input_file.write('First Column:  X\n')
        input_file.write('Second Column: Y\n')
        input_file.write('X Units:  Wavelength (micrometers)\n')
        input_file.write('Y Units:  Reflectance (percent)\n')
        input_file.write('First X Value:\n')
        input_file.write('Last X Value:\n')
        input_file.write('Number of X Values:\n')
        input_file.write('Additional Information:\n')
        input_file.write('\n')
        j = 0
        spectra_values_file.close()
        #Read in values saved in SpectraValues.txt and output them to the library_filename
        spectra_values_file = open('SpectraValues.txt','r')
        while(j < line_count):
            spectra_wave_length = spectra_values_file.readline()
            input_file.write(spectra_wave_length)
            j = j+1
        #Close all open files
        input_file.close()
        spectra_values_file.close()
        #Rename library_filename to match ASTER .spectrum.txt file format
        os.rename(library_filename,library_filename + '.spectrum.txt')
        #Remove temporary file for storing wavelength data
        os.remove('SpectraValues.txt')
        print("Successfully converted file " + library_filename)

class FullSpectralLibrary7Convert:
    def __init__(self):
        """
            This class method converts the entire `USGS Spectral Library Version 7
            <https://speclab.cr.usgs.gov/spectral-lib.html>`_ library into
            its convolved envi format
            
            Args:
            none
            """
        pass

    @classmethod
    def convert(cls, library_filename=""):
        """
            This class method converts the entire `USGS Spectral Library Version 7
            <https://speclab.cr.usgs.gov/spectral-lib.html>`_ library into
            its convolved envi format
            
            Spectral Library Version 7 can be downloaded `here <https://speclab.cr.usgs.gov/spectral-lib.html>`_
            
            Args:
            library_filename (str): path to USGS Spectral Library Version 7 directory
            """
        if not library_filename:
            raise ValueError("Must provide path for USGS Spectral Library Version 7.")
        
        #This will take all the necessary .txt files for spectra in USGS
        #Spectral Library Version 7 and put them in a new directory called
        #"usgs_splib07_modified" in the examples directory
        directory = 'usgs_splib07_modified'
        if not os.path.exists(directory):
            os.makedirs(directory)

        for root, dir, files in os.walk(library_filename + "/ASCIIdata"):
            dir[:] = [d for d in dir]
            for items in fnmatch.filter(files, "*.txt"):
                if "Bandpass" not in items:
                    if "errorbars" not in items:
                        if "Wave" not in items:
                            if "SpectraValues" not in items:
                                shutil.copy2(os.path.join(root,items), directory)

        #This will take the .txt files for Spectra in USGS Spectral Version 7 and
        #convert their format to match that of ASTER .spectrum.txt files for spectra
        # create a new mineral aster conversion instance
        spectral_aster = mineral.SpectralToAsterConversion()
        #List to check for duplicates
        spectra_list = []
        # Convert all files
        files = os.listdir(directory +'/')
        for x in range(0, len(files)):
            name = directory+'/' + files[x]
            #Get name
            input_file = open(name,'r')
            spectra_line = input_file.readline()
            spectra_cut = spectra_line[23:]
            spectra_name = spectra_cut[:-14]
            #Remove first and last char in case extra spaces are added
            spectra_first_space = spectra_name[1:]
            spectra_last_space = spectra_first_space[:-1]
            
            #Check if Spectra is unique
            set_spectra = set(spectra_list)
            if not any(spectra_name in s for s in set_spectra):
                if not any(spectra_last_space in a for a in set_spectra):
                    spectral_aster.convert(name)
                    spectra_list.append(spectra_name)

        set_spectra = set(spectra_list)
        print(set_spectra)

        #This will generate three files s07av95a_envi.hdr, s07av95a_envi.hdr.sli,splib.db and dataSplib07.db
        #For a library in `ASTER Spectral Library Version 2.0 <https://asterweb.jpl.nasa.gov/>`_ format
        data_dir = "dataSplib07.db"
        header_name = "s07av95a_envi"

        # create a new mineral aster conversion instance
        spectral_envi = mineral.AsterConversion()
        # Generate .sli and .hdr
        spectral_envi.convert(directory,data_dir,header_name)


