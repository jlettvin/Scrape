#! /usr/bin/env python

###############################################################################
__date__       = "20130301"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "Trade Secret"
__status__     = "Production"
__version__    = "0.0.1"

"""
GunuPlot3D.py

Implementes a dynamic scientific 3D visualizer class.

See __main__ for an example of use.

TODO: keyboard input requires changing focus back to window of launching app.
"""

import os
from sys import stdout, stderr

from subprocess import *
from scipy import *

platform = os.uname()[0]

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class GnuPlot3D(dict):

    #**************************************************************************
    def __init__(self, **kw):
        self['width' ] = 300
        self['height'] = 400
        self['term'  ] = 'wxt'
        self['keep'  ] = True
        self.update(kw)

    #**************************************************************************
    def __enter__(self):
        args = ["/usr/local/bin/gnuplot"]
        self.pipe = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        self.cmd  = "splot '-' using 1:2:3 with points lt -1 ps 0.5 pt 7\n"
        return self

    #**************************************************************************
    def __exit__(self, aType, aValue, aTraceback):
        if not self['keep']:
            try:
                self.pipe.kill()
            except OSError:
                pass

    #**************************************************************************
    def unitcube(self): # Initialize ranges
        for line in [
                "set xrange[-1:+1]\n",
                "set yrange[-1:+1]\n",
                "set zrange[-1:+1]\n",
                "set terminal %s size %d,%d\n" %
                (self['term'], self['width'], self['height'])]:
            self.send(line)

    #**************************************************************************
    def send(self, line):
        self.pipe.stdin.write(line)

    #**************************************************************************
    def recv(self):
        self.pipe.stdout.read()

    #**************************************************************************
    def points(self, data):
        self.send(self.cmd)
        for x,y,z in data: self.send("%f %f %f\n" % (x,y,z))
        self.send("e\n")

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":
    """
    test illustrates a single point traversing from one cube corner to another.
    """

    #**************************************************************************
    def test():
        with GnuPlot3D() as gp:
            gp.unitcube()
            for j in range(5):
                print j
                for i in arange(-1.0,+1.0,1e-2):
                    gp.points([(i,i,i)])

    #()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
    test()

###############################################################################
# GnuPlot3D.py <EOF>
###############################################################################
