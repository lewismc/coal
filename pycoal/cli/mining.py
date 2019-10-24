# Copyright (C) 2017-2019 COAL Developers
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
# encoding: utf-8

PROGRAM_DESCRIPTION = '''
pycoal-mining -- a CLI for COAL mining classification

pycoal-mining provides a CLI which demonstrates how the COAL Mining 
Classification
API provides methods for generating mining classified images.
Mining classification runtime depends largely on the size of the spectral
library and the available computing resources. More reading an this example 
can be seen at
https://capstone-coal.github.io/docs#usage

@author:     COAL Developers

@copyright:  Copyright (C) 2017-2019 COAL Developers

@license:    GNU General Public License version 2

@contact:    coal-capstone@googlegroups.com
'''

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pycoal.mining import MiningClassification


def main():  # IGNORE:C0111
    # Setup argument parser
    parser = ArgumentParser(description=PROGRAM_DESCRIPTION,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-mi", "--mineral_input", dest="input",
                        help="Input classified mineral file to be processed")
    parser.add_argument("-mo", "--mining_output", dest="output",
                        help="Output mining classified image filename")
    parser.add_argument("-v", "--spectral_version", dest="spectral_version",
                        help="USGS Spectral Library Version Number (6 or 7)")

    # Process arguments
    args = parser.parse_args()

    mineral_filename = args.input
    mining_filename = args.output
    spectral_version = args.spectral_version

    # create a new mining classification instance
    mining_classification = MiningClassification()

    # generate a mining classified image
    mining_classification.classify_image(mineral_filename, mining_filename,
                                         spectral_version)


if __name__ == '__main__':
    main()
