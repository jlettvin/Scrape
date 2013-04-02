#!/usr/bin/env python

###############################################################################
import sys
import Image
import scipy
import numpy as np

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class GIFt(dict):

    #--------------------------------------------------------------------------
    def __init__(self, **kw):
        self.data = []
        self.kw   = kw

    #--------------------------------------------------------------------------
    def __next(self):
        try:
            self.source.seek(self.source.tell()+1)
            return True
        except:
            return False

    #--------------------------------------------------------------------------
    def __get(self):
        data = list(self.source.getdata())
        N = len(data)
        edge = int(scipy.sqrt(N))
        shape = (edge, edge)
        data = (scipy.array(data, dtype=float).reshape(shape)/127.0) - 1.0
        pos, neg = scipy.zeros(shape), scipy.zeros(shape)
        pos[data>0.0] = data[data>0.0]
        neg[data<0.0] = data[data<0.0]
        pos = +pos / pos.sum()
        neg = -neg / neg.sum()
        self.data.append(pos+neg)

    #--------------------------------------------------------------------------
    def __put(self):
        pass

    #--------------------------------------------------------------------------
    def __filename(self, basename, dx, dy, r):
        DX, DY, R = int(dx)*100, int(dy)*100, int(r)*100
        name = "%s.%02d.%02d.%04d.gif" % (basename, DX, DY, R)
        return name

    #--------------------------------------------------------------------------
    def load(self, basename, dx, dy, r):
        self.name = self.__filename(basename, dx, dy, r)
        self.fobj = open(self.name)
        self.source = Image.open(self.fobj)
        if self.source:
            self.__get()
            while self.__next(): self.__get()
            N = len(self.data)
            for n in range(N):
                key  = float(n) / float(N)
                key -= 0 if (key <= 0.5) else 1.0
                key *= 2.0 * scipy.pi
                self[key] = self.data[n]
            del self.source
            self.fobj.close()
        return self

    #--------------------------------------------------------------------------
    def save(self, basename, dx, dy, r):
        self.name = self.__filename(basename, dx, dy, r)
        element0 = self.get(0.0, False)
        assert element0
        assert isinstance(element0, np.ndarray)

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":
    gift = GIFt()
    kernel = gift.load("spine/spine", 0, 0, 1)
    print sys.argv[0]
    for key in sorted(kernel.keys()):
        print "\t", key, kernel[key].sum(), "\n", kernel[key]
###############################################################################
