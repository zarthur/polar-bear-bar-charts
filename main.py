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


def time_compare(result, current_time):
    """Compare the time, in UTC, of a result with the time one hour ago,
    in UTC.  If the year, month, day, and hour are the same, return True
    and the result time.
    """

    compare_time = (current_time.year, current_time.month, current_time.day, 
                    current_time.hour)
    result_time =  datetime.datetime.strptime(result['created_at'],
                                              '%a, %d %b %Y %H:%M:%S %z')
    result_compare = (result_time.year, result_time.month, result_time.day,
                      result_time.hour)
    
    return compare_time == result_compare


def get_polar_data(data, url_template):
    """Get reddit JSON data."""
    # reset month total at the beginning of the month
    current_time = datetime.datetime.now(datetime.timezone.utc) -\
                   datetime.timedelta(hours=1)
    if current_time.day == 1 and current_time.hour == 0:
        data['monthly'][current_time.month] = 0

    page = 1
    count = 0
    while True:
        try:
            url = url_template.format(page=str(page))
            response = get_response(url)['results']
        except:
            break
            
        count += len([result for result in response 
                      if time_compare(result, current_time)])
        page += 1
    
    data['monthly'][current_time.month] += count
    data['hourly'][current_time.hour] = count
    data['current_time'] = current_time

    return data


def load_data(data_path):
    """Load saved data from file."""
    data_default = {'hourly': {x: 0 for x in range(24)},
                    'monthly': {x: 0 for x in range(1, 13)}}

    try:
        with open(data_path) as infile:
            data = yaml.load(infile)
    except IOError:
        data = data_default

    return data


def save_data(data, path):
    """Save data to file."""
    with open(path, 'w') as outfile:
        yaml.dump(data, stream=outfile)


def update(path, url):
    """Update data.  This will load the data file, download and process
    results, and save the data file.
    """
    data = load_data(path)
    data = get_polar_data(data, url)
    save_data(data, path)

    return data


def generate_graphs(data, path=None):
    """Generate and save plots from data.  
    See http://matplotlib.org/examples/pylab_examples/polar_bar.html 
    for more details.
    """
    titles = {'hourly': 'Hourly (UTC, Last 24 hours)',
              'monthly': 'Monthly (Last 12 months)'}
    current_time = data.pop('current_time')
    
    for key in data.keys():
        time, values = zip(*sorted(list(data[key].items())))
        
        fig = pylab.figure()
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
        
        N = len(values)
        theta = pylab.arange(0.0, 2*pylab.pi, 2*pylab.pi / N)
        width = pylab.pi / (N / 2) 
        bars = ax.bar(theta - width /2 , values, width=width, bottom=0.0)
        
        for bartime, val, bar in zip(time, values, bars):
            color = [random.random() for x in range(3)]
            bar.set_facecolor(color)

            if (key == 'hourly' and bartime == current_time.hour) or \
                    (key == 'monthly' and bartime == current_time.month):
                bar.set_linewidth(4)

        ax.set_title(titles[key])
        ax.xaxis.set_major_locator(pylab.FixedLocator(theta))
        ax.set_xticklabels(time)

        filename = "{key}.png".format(key=key)
        filename = os.path.join(path, filename)
        fig.savefig(filename)


def main(path=None, url=None):
    path = path if path else os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(path, 'data')
    web_path = os.path.join(path, 'web')

    url = url if url else "http://search.twitter.com/search.json"\
                "?q=%22polar%20bear%22&result_type=mixed&rpp=100"\
                "&page={page}"

    try:
        data = update(data_file_path, url)
    except urllib.error.HTTPError:
        print('unable to update', file=sys.stderr)
        sys.exit(1)

    generate_graphs(data, web_path)


if __name__ == "__main__":
    main()
