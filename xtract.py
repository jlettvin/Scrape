#!/usr/bin/env python

###############################################################################
__date__       = "20130301"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"
__version__    = "0.0.1"

"""
xtract.py

Implementes movie scraper from web pages listed in cut/paste listener file.

Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

See __main__ for an example of use.
"""

import os, sys, urllib
import cPickle

import pyperclip

class Get:

    #**************************************************************************
    def __init__(self):
        self.types = ['.flv', '.mpg', '.mp4', '.mpeg', '.avi', '.wmv', '.mov']
        self.assoc = dict()
        self.store = "xtract.pkl"
        if os.path.exists(self.store):
            with open(self.store, 'r') as source:
                self.assoc.update(cPickle.load(source))

    #**************************************************************************
    def __call__(self, name, stream):
        # TODO make a dictionary of received files and incorporate xclip
        self.name = name.strip()
        self.clip = None
        self.stream = stream
        found, already = False, False
        for line in stream:
            for field in line.split("&amp;"):
                if "flv_url" in field:
                    url = urllib.unquote(field[8:])
                    for subfield in url.split('/'):
                        for t in self.types:
                            if t in subfield:
                                found = True
                        if found:
                            self.filesize = 0
                            self.filename = subfield.split('?')[0].strip()
                            self.exists = os.path.exists(self.filename)
                            self.percent = "  0%:"
                            self.pct = 0

                            self.current = self.assoc.get(
                                    self.filename,
                                    {'name':name, 'url':url, 'pct':0, 'size':0})
                            self.refresh = True # Should be False

                            if self.current['pct'] != 100:
                                self.assoc[self.filename] = self.current
                                with open(self.store, 'w') as target:
                                    cPickle.dump(self.assoc, target)
                                if self.current['pct'] != 100:
                                    urllib.urlretrieve(
                                            url, self.filename, self.report)
                                self.refresh = True

                            if self.refresh:
                                if self.filesize == 0:
                                    if os.path.exists(self.filename):
                                        self.filesize = os.path.getsize(
                                                self.filename)
                                self.assoc[self.filename] = {
                                        'name':name,
                                        'url':url,
                                        'pct':100,
                                        'size':self.filesize}
                                with open(self.store, 'w') as target:
                                    cPickle.dump(self.assoc, target)
                            print ' '*79,'\r','100%', self.name

    #**************************************************************************
    def report(self, count, size, filesize):
        self.filesize = filesize
        self.percent = "%3d%%:" % (100 * count * size / filesize)
        self.mode    = "(old)" if self.exists else "(new)"
        print self.percent, self.filename, self.name, '\r',
        sys.stdout.flush()

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":

    if len(sys.argv) == 2:
        getter = Get()
        arg = sys.argv[1]
        if os.path.exists(arg):
            for line in open(arg, 'r'):
                line = line.strip()
                if line.startswith('#') or line == "":
                    continue
                getter(line, urllib.urlopen(line))
        else:
            getter(line, urllib.urlopen(line))
