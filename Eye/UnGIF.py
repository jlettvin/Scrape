#!/usr/bin/env python

import Image
import scipy

class UnGIF(dict):

    def next(self):
        try:
            self.source.seek(self.source.tell()+1)
            return True
        except:
            return False

    def fetch(self):
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

    def __init__(self, gifname, *args, **kw):
        self.name = gifname + ".gif"
        self.data = []

    def __enter__(self):
        self.fobj = open(self.name)
        self.source = Image.open(self.fobj)
        self.fetch()
        while self.next(): self.fetch()
        N = len(self.data)
        for n in range(N):
            self[2.0 * scipy.pi * n / N] = self.data[n]
        return self

    def __exit__(self, aType, aValue, aTraceback):
        del self.source
        self.fobj.close()

if __name__ == "__main__":
    with UnGIF("spine/spine.00.00.0100") as kernel:
        for key in sorted(kernel.keys()):
            print "\t", key, kernel[key].sum(), "\n", kernel[key]
