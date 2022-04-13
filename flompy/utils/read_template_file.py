#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Loads information from Template file to a dictionary

Copyright (C) 2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Karamvasis Kleanthis
Last edit: 13.4.2022

This file is part of FLOMPY - FLOod Mapping PYthon toolbox.

    FLOMPY is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FLOMPY is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FLOMPY. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################
import os

def read_template(fname, delimiter='='):
    '''
    Reads the template file into a python dictionary structure.

    Args:
        fname (str): full path to the template file.
        delimiter (str, optional): string to separate the key and value. Defaults to '='.

    Returns:
        template_dict (dict): python dictionary with information from template file

    '''
    template_dict = {}

    if os.path.isfile(fname):
        f = open(fname, 'r')
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # split on the 1st occurrence of delimiter
        c = [i.strip() for i in line.split(delimiter, 1)]
        if line !='': # skip empty lines
            if not len(c) < 2 or not line.startswith(('%', '#')):
    
                atrName = c[0]
                atrValue = str.replace(c[1], '\n', '').split("#")[0].strip()
                atrValue = os.path.expanduser(atrValue)
                atrValue = os.path.expandvars(atrValue)
    
                if atrValue != '':
                    template_dict[atrName] = atrValue
    if os.path.isfile(fname):
        f.close()

    return template_dict

