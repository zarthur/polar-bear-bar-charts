#!/usr/bin/env python3

"""Calculate, load, and store polar-bear-related tweet information.
Requires Python 3.

This should be run hourly to find new tweets.  Tweets from the previous
hour are used.

Hourly totals are replaced each day.  Monthly totals are replaced each
year.
"""

import datetime
import json
import os
import pylab
import random
import sys

import urllib.request

import yaml

def get_response(req_url, json_resp=True):
    """Get response from a sepecified URL; process JSON if response
    is JSON, else return data from URL request.
    """
    request = urllib.request.Request(req_url)
    req_data = urllib.request.urlopen(request)
    data = json.loads(req_data.read().decode()) \
            if json_resp else req_data
    return data


def load_file(path, default):
    """Load JSON data from a file.  If the file does not exist, return
    specified default value."""
    try:
        with open(path) as infile:
            data = yaml.load(infile)
    except IOError:
        data = default

    return data


def save_file(path, content):
    """Save data to file using JSON"""
    with open(path, 'w') as outfile:
        yaml.dump(content, stream=outfile)

def time_compare(result):
    """Compare the time, in UTC, of a result with the time one hour ago,
    in UTC.  If the year, month, day, and hour are the same, return True
    and the result time.
    """

    compare = datetime.datetime.now(datetime.timezone.utc) -\
              datetime.timedelta(hours=1)
    compare_time = (compare.year, compare.month, compare.day, compare.hour)

    result_time =  datetime.datetime.strptime(result['created_at'],
                                              '%a, %d %b %Y %H:%M:%S %z')
    result_compare = (result_time.year, result_time.month, result_time.day,
                      result_time.hour)
    # print(compare_time == result_compare, result_compare, compare_time)
    return compare_time == result_compare, result_time

class PolarStats():
    """Provides methods for loading, saving, updating, and plotting data."""

    def __init__(self, data_path=None, url=None):
        """Set path and source url, initialize data container."""
        file_path = os.path.dirname(os.path.realpath(__file__))
        self._data_path = data_path if data_path else file_path
        self._data_file_path = os.path.join(self._data_path, 'data')

        self._url = url if url else "http://search.twitter.com/search.json"\
                    "?q=%22polar%20bear%22&result_type=mixed&rpp=100"\
                    "&page={page}"

        self._data = None

    def get_polar_data(self):
        """Get reddit JSON data."""
        page = 1
        hourly = 0
        monthly = 0
        result_time = None

        while True:
            try:
                url = self._url.format(page=str(page))
                response = get_response(url)['results']
            except:
                break
                
            for result in response:
                result_has_date, result_time = time_compare(result)
                if result_has_date:
                    has_date = True
                    self._data['monthly'][result_time.month] += 1
                    self._data['hourly'][result_time.hour] += 1

            page += 1

        # define result time if no results are returned
        result_time = result_time if result_time else \
                      datetime.datetime.now(datetime.timezone.utc) -\
                      datetime.timedelta(hours=1)
        
        # reset month at the beginning of the month
        if result_time.day == 1 and result_time.hour == 0:
            self._data['monthly'][result_time.month] = 0

        self._data['monthly'][result_time.month] += monthly
        self._data['hourly'][result_time.hour] = hourly

    def load_data(self):
        """Load saved data from file."""
        data_default = {'hourly': {x: 0 for x in range(24)},
                        'monthly': {x: 0 for x in range(1, 13)}}
        self._data = load_file(self._data_file_path, data_default)

    def save_data(self):
        """Save data to file."""
        save_file(self._data_file_path, self._data)

    def update(self):
        """Update data.  This will load the data file, download and process
        results, and save the data file.
        """
        if not self._data:
            self.load_data()
        self.get_polar_data()
        self.save_data()

    def generate_graphs(self, path=None):
        """Generate and save plots from data.  
        See http://matplotlib.org/examples/pylab_examples/polar_bar.html 
        for more details.
        """
        path = path if path else os.path.join(self._data_path, 'web')

        titles = {'hourly': 'Hourly (Last 24 hours)',
                  'monthly': 'Monthly (Last 12 months)'}

        for key in self._data.keys():
            time, values = zip(*self._data[key].items())
            
            fig = pylab.figure()
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
            
            N = len(values)
            theta = pylab.arange(0.0, 2*pylab.pi, 2*pylab.pi / N)
            width = pylab.pi / (N / 2) 
            bars = ax.bar(theta - width /2 , values, width=width, bottom=0.0)
            
            for val, bar in zip(values, bars):
                color = [random.random() for x in range(3)]
                bar.set_facecolor(color)

            ax.set_title(titles[key])
            ax.xaxis.set_major_locator(pylab.FixedLocator(theta))
            ax.set_xticklabels(time)

            filename = "{key}.png".format(key=key)
            filename = os.path.join(path, filename)
            fig.savefig(filename)


def main():
    """Update data and generate new plots."""
    polar = PolarStats()
    try:
        polar.update()
    except urllib.error.HTTPError:
        print('unable to update', file=sys.stderr)

    polar.generate_graphs()

if __name__ == "__main__":
    main()
