#!/usr/bin/env python3

"""Calculate, load, and store average polar-bear-related tweet information.
Requires Python 3.

This should be run hourly to find new tweets.  Tweets from the previous
hour are used.
"""

import datetime
import json
import os
import pylab
import sys

import urllib.request

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
    try:
        with open(path) as infile:
            data = json.load(infile)
    except IOError:
        data = default

    return data


def save_file(path, content):
    with open(path, 'w') as outfile:
        json.dump(content, outfile)

def time_compare(result):
    compare = datetime.datetime.now(datetime.timezone.utc) -\
              datetime.timedelta(hours=1)
    compare_time = (compare.year, compare.month, compare.day, compare.hour)

    result_time =  datetime.datetime.strptime(result['created_at'],
                                              '%a, %d %b %Y %H:%M:%S %z')
    result_compare = (result_time.year, result_time.month, result_time.day,
                      result_time.hour)

    return compare_time == result_compare, result_time

class PolarStats():
    """Container for data and associated methods."""

    def __init__(self, data_path=None, url=None):
        """Set path and source url, initialize data container."""
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        self._data_path = data_path if data_path else \
                          os.path.join(home, '.polar-stats')
        self._data_file_path = os.path.join(self._data_path, 'data')
        if not os.path.exists(self._data_path):
            os.makedirs(self.data_path)

        self._url = url if url else "http://search.twitter.com/search.json"\
                    "?q=%22polar%20bear%22&result_type=mixed&rpp=100"\
                    "&page={page}"

        self._data = None

    def get_polar_data(self):
        """Get reddit JSON data."""
        has_date = True
        page = 1
        while has_date:
            url = self._url.format(page=str(page))
            response = get_response(url)['results']
            
            # always get first 1000 results
            has_date = True if page <= 10 else False
            for result in response:
                result_has_date, result_time = time_compare(result)
                if result_has_date:
                    has_date = True
                    self._data['monthly'][str(result_time.month)] += 1
                    self._data['hourly'][str(result_time.hour)] += 1

            page += 1

    def load_data(self):
        """Load saved data from file."""
        data_default = {'hourly': {str(x): 0 for x in range(24)},
                        'monthly': {str(x): 0 for x in range(1, 13)}}
        self._data = load_file(self._data_file_path, data_default)

    def save_data(self):
        """Save data to file."""
        save_file(self._data_file_path, self._data)

    def update(self):
        if not self._data:
            self.load_data()
        self.get_polar_data()
        self.save_data()

    def generate_graphs(self):
        """Generate and save plots from data."""
        Ns = {'hourly': 24, 'monthly': 12}
        for key in self._data.keys():
            hour, values = zip(*data[key].items())
            radius = max(values)
            values = [x / radius for x in values]           
            fig = pylab.figure()
            ax = fig.add_axes(polar=True)
            N = Ns[key]
            theta = numpy.arange(0.0, 2*numpy.pi, 2*numpy.pi / N)
            width = np.pi / (2 * N)
            bars = ax.bar(theta, radius, width=width, bottom=0.0)
            fig.savefig(''.join([self._data_path, key, '.jpg']))


def main():
    polar = PolarStats()
    try:
        polar.update()
    except urllib.error.HTTPError:
        print('unable to update', file=sys.stderr)

    # polar.generate_graphs(DATA_PATH)

if __name__ == "__main__":
    main()
