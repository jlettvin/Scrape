#!/usr/bin/env python

"""
Spines.py

Implements rings of VGS (vector gradient samplers).
An Airy disk has a very sharp circle of zero value at a very precise radius.

Image pixelation is imposed, and all calculation is constrained by the mesh.
Pixels have non-zero extent and average around the zero, leaving a blur.
A kernel detects presence of a 0-arc in the midst of a brighter surround,
and detects presence of a 1-arc in the midst of a darker surround,
despite the pixel sampling blur.

Given a radius, a set of kernels (NxN coefficient arrays) are produced.
N is the edge size of the single spine convolution kernel.
The value of angle(+x,y*1.0j) gives the radians direction for a VGS.
The value of angle(-y,x*1.0j) gives the tangent of the circle at VGS.
A kernel sums to 0.0, the tangent pixels sum to -1.0, other pixels sum to +1.0.

A convolved kernel averages pixels around the tangent point.
If the value is more positive than a positive threshold, a 0-arc is "detected".
If the value is more negative than a negative threshold, a 1-arc is "detected".
Detection is +1.0 or -1.0.  Non-detection is 0.0.  No other values are allowed.

The eventual goal is to detect coincidences of like arc detections by
summing arc kernel results over the entire circle and thresholding sums
for positive and negative values to declare presence of a filter "match".

Spines.py creates the kernels and stores them in animated GIF files.
UnGIF.py reads these files and converts the frames back into kernels.
"""

#******************************************************************************
import os, sys

from scipy import *
from scipy.misc import *
from itertools import *

from UnGIF import *

#******************************************************************************
class Spines:

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, R, **kw):

        # fetch parameters
        C = kw.get('coefficient', 1.0)  # Decay rate of Gaussian
        N = kw.get('miniedge', 5)       # Size of convolution kernel
        dx = kw.get('dx', 0.0)          # Displacement of diffraction center
        dy = kw.get('dy', 0.0)          # Displacement of diffraction center

        # validate parameters
        assert(1e-1 < C < 1e1)                              # C around 1.0
        # 3 when bright, 7 when dark, 5 between
        assert(2 < N < 8 and (N%2) == 1)                    # N must be 3|5|7
        assert(-0.5 <= dx <= +0.5 and -0.5 <= dy <= +0.5)   # dx within pixel

        # calculate maximum orthogonal displacement of NxN pixel
        dR = N/2
        R = float(R)
        # dictionary of NxN pixel squares surrounding bounding circle pixels
        self.spine = {}
        # incremental radii for bounding usable pixels
        RN1, RP1 = arange(R-0.5, R+0.6, 1.0)
        # odd edge length of the bounding square for symmetry around (0,0)
        self.edge = 1 + 2 * int(RP1)
        # coordinates of discrete pixels forming circle around (0,0)
        self.circle = [(X, Y, float(X-R), float(Y-R)) for X, Y in
                # starting from all pixels within the bounding square
                list(product(range(int(self.edge)), repeat=2))
                # then excluding those not within the nearer bounding radii
                if self.adjacent(float(X-R), float(Y-R), RN1, RP1)]
        # for each pixel along the bounding circle
        for X, Y, x, y in self.circle:
            # slope of the circle tangent
            tangent = (-y,x)
            # generate a NxN square of coordinates surrounding the pixel
            square = array(
                    list(
                        product(
                            arange(x-dx-dR, x-dx+dR+1), # - for LR
                            arange(y+dy-dR, y+dy+dR+1)  # + for DU
                               )
                        )
                          ).reshape((N,N,2))
            # prefilled NxN squares of coefficients for each coordinate pair
            neg, pos = zeros((N,N), dtype=float), zeros((N,N), dtype=float)
            # over NxN square indices
            for y0, x0 in list(product(range(N), repeat=2)):
                # fetch the coordinates of the pixel within the NxN square
                x1, y1 = square[x0, y0]
                # determine proximity to tangent line
                adjacent = self.adjacent(x1, y1, RN1, RP1)
                # calculate radius to these coordinates
                r = self.radius(x1, y1)
                # calculate coefficient for this distance from tangent line
                coeff = exp(-C*(r-R)**2)
                # fill pixel in NxN coefficent set with gross estimate
                (pos if adjacent else neg)[x0,y0] = coeff
            # calculate the angle to the central pixel
            theta = pi + angle(-y+x*1.0j)
            theta = 0.0 if theta == 2.0 * pi else theta
            # Normalize the sums of the pos and neg arrays (kernel sums to 0)
            pos, neg = -pos / pos.sum(), neg / neg.sum()
            # combine the coefficients into a convolution kernel
            self.spine[theta] = {'coeff': pos + neg, 'coord': square}
            # create a copy that can be adjusted for use as a PNG image
            if kw.get('saving', False):
                self.save(R, theta, dx, dy, self.spine[theta])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def radius(self, x, y):
        return sqrt(x*x + y*y)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def adjacent(self, x, y, RN, RP):
        """Adjacency test"""
        return (RN <= self.radius(x,y) <= RP)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def save(self, r, theta, dx, dy, circle):
        kernel = circle['coeff']
        aNxN = (1.0 + kernel.copy()) * 127.0
        # calculate the label values
        Rval, Tval = int(r*100), int(theta*100)
        dXval, dYval = int(dx*100), int(dy*100)
        # save the kernel as a PNG
        toimage(aNxN, cmin=0, cmax=254).save(
                'spine/spine.%02d.%02d.%04d.%03d.png' % (dXval,dYval,Rval,Tval))
        if dXval == 0 and dYval == 0 and Rval == 100:
            print kernel

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def gif(self, r, dx, dy, **kw):
        r100 = r * 100
        dx100, dy100 = dx * 100, dy * 100
        partial = "spine/spine.%02d.%02d.%04d" % (dx100,dy100,r100)
        source = partial+".*.png"
        target = partial+".gif"
        command = (
                "convert"
                " -set"+
                " delay 10"+
                " -dispose 0"+
                " -loop 0"+
                " "+source+
                " "+target)
        if kw.get('verbose', False):
            print command, '\r',
            sys.stdout.flush()
        os.system(command)
        os.system("rm "+source)
        return len(command)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @property
    def aNxN(self, r, theta):
        """A circle of square pairs of coeff and coord by theta"""
        return self.spine[theta]

#******************************************************************************
if __name__ == "__main__":
    verbose = False
    spines, N = {}, 0
    for (dx,dy) in [(0.0,0.0), (0.4,0.4)]:
        for radius in arange(1.0, 13.0, 0.5):
            label = '%f.%f.%f' % (dx, dy, radius)
            spines[label] = Spines(
                    radius,                     # diffraction radius
                    miniedge=5,                 # size of convolution kernel
                    coefficient=1.0,            # Gaussian decay rate
                    dx=dx,                      # off-center within NxN pixel
                    dy=dy,                      # off-center within NxN pixel
                    saving=True)                # save kernel images in spine/
            spines[label].gif(radius, dx, dy, verbose=verbose)
    if verbose:
        print

#******************************************************************************
