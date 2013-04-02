#!/usr/bin/env python

import os, sys
import termios
import fcntl
import random
import scipy
import itertools
import select
import pprint

from optparse import OptionParser

from GnuPlot3D import GnuPlot3D
from Raw import Raw

class Sphere(object):
    def signed(self):
        return (random.random()*2.0)-1.0

    def xyz(self, x,y,z):
        return scipy.array([
            self.signed(),self.signed(),self.signed(),
            0.0,0.0,0.0,
            x,y,z])

    def save(self, name):
        with open(name, "w") as target:
            for p in self.point:
                print>>target, "%f, %f, %f" % (p[0], p[1], p[2])

    def load(self, count):
        if not count:
            return
        try:
            name = "Spheres.%d.xyz" % (count)
            print 'loading:', name
            self.point = []
            with open(name) as source:
                self.point = [
                        scipy.array(
                        list(eval(line)) + [0.0]*6)
                        for line in source]
            p = self.point[0]
            self.radius = scipy.sqrt(p[0]**2+p[1]**2+p[2]**2)
            self.count = len(self.point)
            assert count == self.count
            self.iteration = 0
            self.point = self.random()
        except:
            print 'loading FAILED'

    def r(self, point):
        x,y,z = point[0:3]
        return scipy.sqrt(x**2+y**2+z**2)

    def random(self):
        # Choose one of 48 rotations/mirrorings.
        # Symmetric axis and sign change.
        c = list(self.swaps[random.randint(0,5)]) # for swaps
        d = list(self.signs[random.randint(0,8)]) # for signs
        result = [scipy.array([
            d[0]*p[c[0]],       # New signed X
            d[1]*p[c[1]],       # New signed Y
            d[2]*p[c[2]],       # New signed Z
            p[3], p[4], p[5], p[6], p[7], p[8]
            ]) for p in self.point]
        return result

    def force(self, p1, p2):
        (x1,y1,z1), (x2,y2,z2) = p1[0:3], p2[0:3]
        dr = scipy.array([x1-x2,y1-y2,z1-z2])
        distance = self.r(dr)
        distance += 1e-6*(distance == 0.0)
        p1[3:6] += self.coeff * dr / distance**2
        p2[3:6] -= self.coeff * dr / distance**2

    def move(self): # Exercise force equation iteratively
        for p in self.point: p[0:3] += p[3:6]    # move due to previous forces
        for p in self.point: p /= self.r(p)      # normalize onto sphere
        #p /= self.radius
        for p in self.point: p[3:6] = 0.0        # zero forces
        for a,b in itertools.combinations(range(len(self.point)), 2):
            self.force(self.point[a], self.point[b])# generate next round forces
        for p in self.point:                     # add heat to the forces
            p[3:6] += [self.signed()*self.heat for n in range(3)]
        self.heat /= 2.0
        if self.pulse and not (self.iteration%self.pulse):
            self.heat += self.hot * float(not self.finish)

    def cycle(self):
        self.move()
        self.keyboard()
        self.iteration += 1
        if self.final and (self.iteration >= self.final):
            self.finish = True
            if self.heat < 1e-6:
                self.live = False

    def keyboard(self):
        if self.kb.kbhit():
            c = self.kb.getch()
            oc = ord(c)
            if   c in "xXqQ":       self.live = False
            elif c in "hH":         self.heat += self.hot
            elif c == '+':          self.add()
            elif c == '-':          self.sub()
            elif c == '*':          self.add(10)
            elif c == '/':          self.sub(10)

    def add(self, count=1):
        assert isinstance(count, int)
        assert 1 <= count <= 256
        for N in range(count):
            present = True
            while present:
                candidate = self.xyz(1,3,4)
                present = False
                for p in self.point:
                    if (p == candidate).all():
                        present = True
                        break
            if not present: self.point += [candidate,]

    def sub(self, count = 1):
        assert isinstance(count, int)
        assert 1 <= count <= 256
        if len(self.point) > (2+count):
            self.point = self.point[:-(count-2)]

    def generate(self):
        print 'generating:'
        self.add(self.count)

    def __init__(self, **kw):
        self.kw = kw
        self.point = []
        self.signs = list(itertools.product([-1.0,+1.0], repeat=3))
        self.swaps = list(itertools.permutations([0,1,2], 3))

    def __call__(self):
        self.iteration  = 0
        self.hot    = 1e2
        self.radius = self.kw.get("radius", 1.0)
        self.verbose= self.kw.get("verbose", False)
        self.count  = self.kw.get("count", 256)
        self.heat   = self.kw.get("heat", 1e3)
        self.coeff  = self.kw.get("coeff", 1e2)
        self.pulse  = self.kw.get("pulse", 0)
        self.final  = self.kw.get("final", 256)
        self.finish = False
        self.live   = True
        if self.verbose:
            pprint.pprint(self.kw)
        if not self.point:
            self.generate()
        with Raw() as self.kb:
            with GnuPlot3D(width=300, height=400) as gp:
                gp.unitcube()
                while self.live:
                    q = [(p[0],p[1],p[2]) for p in self.point]
                    gp.points(q)
                    gp.send('set label "Spheres" at -1,-1,-1\n')
                    self.cycle()
            self.save("Spheres.%d.xyz" % self.count)

if __name__ == "__main__":
    kw = { "show": True, "count": 100, "radius": 0.3, "pulse": 10 }
    parser = OptionParser()
    parser.add_option( "-l", "--load",
            type=int, default=0,
            help="collection of existing points")
    parser.add_option( "-f", "--final",
            type=int, default=256,
            help="number of points to distribute over sphere")
    parser.add_option( "-N", "--count",
            type=int, default=100,
            help="number of points to distribute over sphere")
    parser.add_option( "-p", "--pulse",
            type=int, default=10,
            help="number of heat pulses to force best minimum energy")
    parser.add_option( "-r", "--radius",
            type=float, default=0.3,
            help="radius of sphere")
    parser.add_option( "-v", "--verbose",
            action="store_true", default=False,
            help="announce actions and sizes")
    (opts, args) = parser.parse_args()
    kw.update(vars(opts))

    sphere = Sphere(**kw)
    sphere.load(opts.load)
    sphere()
