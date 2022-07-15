#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
from .exceptions import NameNotInTimeSeriesError, MinMaxCloudBoundError, MinMaxDateError

class timeseries():
    """Base class of time series objects."""
    
    def __init__(self, name):
        self.name = name
        self.data = []
        self.names = []
        self.dates = []
        self.cloud_cover = []
        self.total = 0

    def show_metadata(self, name = None):
        """Prints all the metadata of all available data of the time series or of a selected image.

        Args:
            name (str, optional): Name of the image to print its metadata. Defaults to None

        Raises:
            NameNotInTimeSeriesError: Raises when the provided name is not in the list of data
        """
        if name == None:
            for image in self.data:
                print(image.__dict__)
        else:
            try:
                index = self.names.index(name)
                print(self.data[index].__dict__)
            except:
                raise NameNotInTimeSeriesError("Provided name is not in the time series object.")
    
    def remove_cloudy(self, max_cloud, min_cloud = 0):
        """Removes from the list of data all the images with cloud coverage that overcomes the
        maximum and minimum bounds provided by the user. 

        Args:
            max_cloud (int): Maximum allowed cloud coverage
            min_cloud (int, optional): Mimimum allowed cloud coverage. Defaults to 0

        Raises:
            MinMaxCloudBoundError: Raises when maximum cloud coverage is less than the minimum coverage
        """
        if max_cloud < min_cloud:
            raise MinMaxCloudBoundError("Maximum cloud coverage value is less than the minimum cloud coverage value.")
        logging.info("Searching for data with cloud coverage less than {:.2f}% and more than {:.2f}%...".format(min_cloud, max_cloud))
        new = []
        for image in self.data:
            if image.cloud_cover == None:
                logging.warning("Image {} has no cloud coverage information stored!".format(image.name))
            elif float(image.cloud_cover) > max_cloud or float(image.cloud_cover) < min_cloud:
                logging.info("Removing {} with cloud coverage {:.2f}...".format(image.name, float(image.cloud_cover)))
                self.names.remove(image.name)
                self.dates.remove(image.datetime)
                self.cloud_cover.remove(image.cloud_cover)
            else:
                new.append(image)
                logging.info("Keeping {} with cloud coverage {:.2f}...".format(image.name, float(image.cloud_cover)))
        self.data = new
        self.total = len(self.data)
        del (new)
        logging.info("New number of data after selecting cloud cover less than {}% and more than {}% is: {}".format(max_cloud, min_cloud, len(self.data)))

    def keep_timerange(self, start_time, end_time):
        """Keeps all the data that are inside the range of a start_time (HHMMSS format) and an end time (HHMMSS format).

        Args:
            start_time (str): Start time in HHMMSS format
            end_time (str): End time in HHMMSS format
        """
        start = datetime.datetime.strptime(start_time, "%H%M%S").time()
        end = datetime.datetime.strptime(end_time, "%H%M%S").time()

        new = []
        for image in self.data:
            if start <= end:
                if (image.datetime.time()) < start or (image.datetime.time()) > end:
                    self.names.remove(image.name)
                    self.dates.remove(image.datetime)
                    self.cloud_cover.remove(image.cloud_cover)
                    logging.info("Removing {} with date {} and time {}...".format(image.name, image.date, image.datetime.time()))
                else:
                    new.append(image)
            else:
                if (image.datetime.time()) < start and (image.datetime.time()) > end:
                    self.names.remove(image.name)
                    self.dates.remove(image.datetime)
                    self.cloud_cover.remove(image.cloud_cover)
                    logging.info("Removing {} with date {} and time {}...".format(image.name, image.date, image.datetime.time())) 
                else:
                    new.append(image)
                    
        self.data = new
        self.total = len(new)
        del (new)
        logging.info("New number of data after removing timerange {}-{} is: {}".format(start, end, self.total))
                
    def remove_date(self, date):
        """Removes from the list of data all the instances with a specific date(s) provided by the user.
        Date format: DDMMYYYY

        Args:
            date (str, list): Date(s) to remove in DDMMYYYY format

        Raises:
            TypeError: Raises if date is not a str or a list
            ValueError: Raises if date value is not a 8 length str
        """
        
        if not isinstance(date, list):
            if not isinstance(date, str):
                raise TypeError("Date must be string or a list of string!")
            else:
                if len(date) != 8:
                    raise ValueError("Date format is DDMMYYYY")
        else:
            for d in date:
                if len(d) != 8:
                    raise ValueError("Date format is DDMMYYYY")
            
        if isinstance(date, list):
            for d in date:
                new = []
                d = datetime.datetime.strptime('{} {} {}'.format(d[0:2], d[2:4], d[4:]), "%d %m %Y").date()
                logging.info("Searching for data ingested sooner than {}...".format(d))
                for image in self.data:
                    if image.date == None:
                        logging.warning("Image {} has no date information stored!".format(image.name))
                    elif image.date == d:
                        logging.info("Removing {} with date {}...".format(image.name, image.date))
                        self.names.remove(image.name)
                        self.dates.remove(image.datetime)
                        self.cloud_cover.remove(image.cloud_cover)
                    else:
                        new.append(image)
                        logging.info("Keeping {} with date {}...".format(image.name, image.date))
                self.data = new
                self.total = len(self.data)
                del (new)
                logging.info("New number of data after removing date {} is: {}".format(d, len(self.data)))
        else:
            new = []
            d = datetime.datetime.strptime('{} {} {}'.format(date[0:2], date[2:4], date[4:]), "%d %m %Y").date()
            logging.info("Searching for data ingested sooner than {}...".format(d))
            for image in self.data:
                if image.date == None:
                    logging.warning("Image {} has no date information stored!".format(image.name))
                elif image.date == d:
                    logging.info("Removing {} with date {}...".format(image.name, image.date))
                    self.names.remove(image.name)
                    self.dates.remove(image.datetime)
                    self.cloud_cover.remove(image.cloud_cover)
                else:
                    new.append(image)
                    logging.info("Keeping {} with date {}...".format(image.name, image.date))
            self.data = new
            self.total = len(self.data)
            del (new)
            logging.info("New number of data after removing date {} is: {}".format(d, len(self.data)))

    def filter_dates(self, max_date, min_date = None):
        """Removes from the list of data all the instances with date more than max_date and less than min_date.
        Date format: DDMMYYYY

        Args:
            max_date (str): Maximum date in DDMMYYY format
            min_date (str, optional): Minimum date in DDMMYYY format. Defaults to None

        Raises:
            TypeError: Raises if max_date is not a str
            ValueError: Raises if max_date is not 8 length str
            TypeError: Raises if min_date is not a str
            ValueError: Raises if min_date is not 8 length str
            MinMaxDateError: Raises if maximum date is sooner than minimum date
        """
        if not isinstance(max_date, str):
            raise TypeError("Date must be string!")
        else:
            if len(max_date) != 8:
                raise ValueError("Date format is DDMMYYYY")
        
        if min_date is None:
            new = []
            max_date = datetime.datetime.strptime('{} {} {}'.format(max_date[0:2], max_date[2:4], max_date[4:]), "%d %m %Y").date()
            logging.info("Searching for data ingested sooner than {}...".format(max_date))
            for image in self.data:
                if image.date == None:
                    logging.warning("Image {} has no date information stored!".format(image.name))
                elif image.date >= max_date:
                    logging.info("Removing {} with date {}...".format(image.name, image.date))
                    self.names.remove(image.name)
                    self.dates.remove(image.datetime)
                    self.cloud_cover.remove(image.cloud_cover)
                else:
                    new.append(image)
                    logging.info("Keeping {} with date {}...".format(image.name, image.date))
            self.data = new
            self.total = len(self.data)
            del (new)
            logging.info("New number of data after selecting date less than {} is: {}".format(max_date, len(self.data)))
        
        else:

            if not isinstance(min_date, str):
                raise TypeError("Date must be string!")
            else:
                if len(min_date) != 8:
                    raise ValueError("Date format is DDMMYYYY")
            
            max_date = datetime.datetime.strptime('{} {} {}'.format(max_date[0:2], max_date[2:4], max_date[4:]), "%d %m %Y").date()
            min_date = datetime.datetime.strptime('{} {} {}'.format(min_date[0:2], min_date[2:4], min_date[4:]), "%d %m %Y").date()

            if max_date <= min_date:
                raise MinMaxDateError("Maximum date is before or the same with minimum date!")
            else:
                new = []
                logging.info("Searching for data ingested sooner than {}...".format(max_date))
                for image in self.data:
                    if image.date == None:
                        logging.warning("Image {} has no date information stored!".format(image.name))
                    elif image.date >= max_date or image.date <= min_date:
                        logging.info("Removing {} with date {}...".format(image.name, image.date))
                        self.names.remove(image.name)
                        self.dates.remove(image.datetime)
                        self.cloud_cover.remove(image.cloud_cover)
                    else:
                        new.append(image)
                        logging.info("Keeping {} with date {}...".format(image.name, image.date))
                self.data = new
                self.total = len(self.data)
                del (new)
                logging.info("New number of data after selecting date less than {} is: {}".format(max_date, len(self.data)))

    def sort_images(self, cloud_coverage = False, date = False):
        """Sort images based on name. If cloud coverage is True then sorts based on cloud coverage.
        If date is True then sorts based on dates.

        Args:
            cloud_coverage (bool, optional): Sort by cloud coverage. Defaults to False
            date(bool, optional): Sort by dates. Defaults to False
        """
        if cloud_coverage is True and date is True:
            logging.warning("Sorting works only with one option!")
            return

        elif cloud_coverage is True and date is False:
            
            # Sort images
            zipped = zip(self.cloud_cover, self.names, self.data)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.data = [i for _, _, i in sorted_list]

            # Sort names
            zipped = zip(self.cloud_cover, self.names)
            sorted_list = sorted(zipped)
            self.names = [i for _, i in sorted_list]
            
            # Sort dates
            zipped = zip(self.cloud_cover, self.names, self.dates)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.dates = [i for _, _, i in sorted_list]

            self.cloud_cover = sorted(self.cloud_cover)                     

        
        elif cloud_coverage is False and date is True:
            # Sort images
            zipped = zip(self.dates, self.names, self.data)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.data = [i for _, _, i in sorted_list]

            # Sort names
            zipped = zip(self.dates, self.names)
            sorted_list = sorted(zipped)
            self.names = [i for _, i in sorted_list]
            
            # Sort cloud cover
            zipped = zip(self.dates, self.names, self.cloud_cover)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.cloud_cover = [i for _, _, i in sorted_list]

            self.dates = sorted(self.dates)

        else:
            # Sort images
            zipped = zip(self.names, self.dates, self.data)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.data = [i for _, _, i in sorted_list]

            # Sort dates
            zipped = zip(self.names, self.dates)
            sorted_list = sorted(zipped)
            self.dates = [i for _, i in sorted_list]

            # Sort cloud cover
            zipped = zip(self.names, self.dates, self.cloud_cover)
            sorted_list = sorted(zipped, key = lambda k: (k[0], k[1]))
            self.cloud_cover = [i for _, _, i in sorted_list]

            # In the end sort the names
            self.names = sorted(self.names)