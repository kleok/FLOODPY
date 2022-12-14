#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

