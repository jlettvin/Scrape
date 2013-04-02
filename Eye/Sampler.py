#!/usr/bin/env python
"""Sampler.py"""

###############################################################################
__date__       = "20130221"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "Trade Secret"
__status__     = "Production"
__version__    = "0.0.1"

###############################################################################
from scipy      import ones, array, sqrt, arange, rot90, fabs, where, around
from scipy      import set_printoptions
from itertools  import product
from optparse   import OptionParser
from subprocess import call

set_printoptions(precision=2, linewidth=500)

class Sampler(object):
    def __init__(self, **kw):
        self.kw = kw

    def __call__(self, xy, rbox = 1):
        px, py = xy         # Position of original point
        sx, sy = py, -px    # Line of orthogonal

        ibox = 1 + 2 * rbox # integer edge of small box
        isqr = ibox * ibox  # integer area of small box
        ifrm = 3 * ibox     # integer edge of large box
        rfrm = ifrm / 2.0
        x0, y0 = rfrm, rfrm

        ffrm = float(rfrm)

        frame = -ones((ifrm, ifrm), dtype=float)

        if px == 0 and py == 0:
            frame[:,:] = -1.0
            frame[ibox:2*ibox,ibox:1+2*ibox] = 0.0
            frame[:,:] /= frame.sum()
            frame[ibox:2*ibox,ibox:1+2*ibox] = 1.0 / isqr
        else:
            blk = product(arange(-ffrm,+ffrm+1.0,1.0), repeat=2)
            print list(blk)
        print frame

if __name__ == "__main__":

    parser = OptionParser()
    #parser.add_option( "--E", default=11.70, type=float, help="max edge length")
    #parser.add_option("--dE", default= 1.00, type=float, help="edge increment")
    #parser.add_option("--dR", default= 0.05, type=float, help="radial increment")

    #parser.add_option("-p", "--plain",
            #action="store_true", default=False,
            #help="make gnuplot file plain, not fancy")

    parser.add_option( "-v", "--verbose",
            action="store_true", default=False,
            help="announce actions and sizes")
    (opts, args) = parser.parse_args()
    kw = vars(opts)

    sampler = Sampler(**kw)
    sampler((0,0))
    sampler((1,0))
