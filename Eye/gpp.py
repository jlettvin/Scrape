#! /usr/bin/env python

from subprocess import *
from scipy import *
from sys import stdout, stderr
from os import linesep as nl

class GnuPlot3D(object):

    def __init__(self, **kw):
        self.width, self.height = kw.get("width", 600), kw.get("height", 600)
        self.keep = kw.get("keep", True)

    def __enter__(self):
        args = ["/usr/local/bin/gnuplot"]
        self.pipe = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE,)
        self.cmd  = "splot '-' using 1:2:3 with points lt -1 ps 0.5 pt 7\n"
        # Initialize ranges
        for line in [
                "set xrange[-1:+1]\n",
                "set yrange[-1:+1]\n",
                "set zrange[-1:+1]\n",
                "set terminal wxt size 600,600\n"]:
            self.send(line)
        return self

    def send(self, line):
        self.pipe.stdin.write(line)

    def recv(self):
        self.pipe.stdout.read()

    def plot(self, data):
        self.send(self.cmd)
        for x,y,z in data: self.send("%f %f %f\n" % (x,y,z))
        self.send("e\n")

    def __exit__(self, aType, aValue, aTraceback):
        if not self.keep:
            try:
                self.pipe.kill()
            except OSError:
                pass

if __name__ == "__main__":
    def plot3D():
        with GnuPlot3D() as gp:
            for j in range(5):
                print j
                for i in arange(-1.0,+1.0,1e-2):
                    gp.plot([(i,i,i)])

    plot3D()
