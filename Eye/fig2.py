#!/usr/bin/env python

# http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp

"""
By setting the color table size to 6 (yielding 2**(6+1) == 128 colors)
the symbol size is 7 bits making CLEAR == \x80, and STOP == \x81
The remainder of the codes \x00 through \x7f are indices into the color table.
For a 5x5 block (25 pixels) or 7x7 (49 pixels) or 9x9 (81 pixels)
the number of colors need not exceed the number of pixels.
So, codes could be \x00 through \x1f for 5x5 with \x20 and \x21 as CLEAR/STOP.
Meanwhile, the colors are 24 bit or >4e6 values.
If colors are ignored, this allows use of signed floating point values
between -2e6 to +2e6 which we can restrict to -1e6 to +1e6.
This allows storage of kernel coefficients in a useful way.
"""

import os

from struct import *

def UByte(N):
    assert isinstance(N, int)
    assert -128 <= N <= +127
    return pack("b", N)

def Byte(N):
    assert isinstance(N, int)
    assert 0 <= N <= 255
    return pack("B", N)

def UWord(N):
    assert isinstance(N, int)
    assert -32768 <= N <= +32767
    return pack("H", N)

def Word(N):
    assert isinstance(N, int)
    assert 0 <= N <= 65535
    return pack("H", N)

def Bytes(Ns):
    assert isinstance(Ns, list)
    result = ""
    for N in Ns:
        result += Byte(N)
    return result

def block(s):
    return Byte(len(s)) + s + Byte(0)

def RGB(r,g,b):
    return Byte(r)+Byte(g)+Byte(b)

class Fig(dict):

    def __init__(self, X, Y, **kw): #loops=0, sleep=200):
        # parameters
        self.bits       = 7
        self.loops      = kw.get("loops", 0)
        self.sleep      = kw.get("sleep", 200)
        self.width      = X
        self.height     = Y
        self.area       = self.width * self.height
        __, FF          = 0x00, 0xff

        # bitfield for GIF Header
        gctf            = 1      # Global color table flag
        res             = 1      # Color resolution
        sort            = 0      # Sort flag
        cts             = self.bits - 1 # Color table size
        pval            = (gctf << 7) | (res  << 4) | (sort << 3) | (cts << 0)

        # bitfield for Graphic Control Extension Block
        rsv             = 0
        disp            = 0
        inp             = 0
        tcf             = 0
        gval            = (rsv  << 6) | (disp << 3) | (inp  << 1) | (tcf << 0)

        # values
        high            = 2 ** self.bits

        # Byte atoms
        self.tail       = Byte(0x00)
        trans           = Byte(0x00)
        self.head       = Byte(0x21)
        sep             = Byte(0x2c)
        exit            = Byte(0x3b)
        label           = Byte(0xf9)
        self.app        = Byte(0xff)
        start           = Byte(self.bits)
        self.clear      = Byte(0 + high)
        self.eoi        = Byte(1 + high)
        Left, Top       = 0, 0

        # Word atoms
        delay           = Word(self.sleep)
        cycle           = Word(self.loops + 1)

        # data
        self['XY']      = Word(self.width)+Word(self.height)

        # entries
        self['K']       = RGB(__,__,__)
        self['R']       = RGB(FF,__,__)
        self['Y']       = RGB(FF,FF,__)
        self['G']       = RGB(__,FF,__)
        self['C']       = RGB(__,FF,FF)
        self['B']       = RGB(__,__,FF)
        self['V']       = RGB(FF,__,FF)
        self['W']       = RGB(FF,FF,FF)

        # fields
        self['INIT']    = "GIF89a" # 89a for GCE
        self['LSD']     = self['XY']+Byte(pval)+Byte(0)+Byte(0)
        self['GCT']     = self.colors("KRYGCBVW")
        self['EXT']     = self.application("NETSCAPE2.0", "\x01") # 1 == forever
        self['GCE']     = self.graphics(UByte(gval)+delay+trans)
        self['IDH']     = sep+Word(Left)+Word(Top)+self['XY']+self.tail

        self['FINI']    = exit

    def graphics(self, data):
        return self.head+Byte(0xf9)+block(data)

    def application(self, vendor="NETSCAPE2.0", data="\x01"):
        result  = self.head+self.app
        result += Byte(len(vendor))+vendor
        result += block(data+Byte(0))
        result += self.tail
        return result

    def colors(self, letters, repeat=16):
        assert isinstance(letters, str)
        result = ""
        for letter in letters:
            print letter
            #assert letter in self.keys()
            result += self[letter]
        return result * repeat

    def frame(self, data, x=0, y=0):
        assert isinstance(data, list) or isinstance(data, str)
        assert len(data) == (self.area)
        result  = ""
        result += self.application("XYOFFSET", UByte(x)+UByte(y))
        result += self['GCE']
        result += self['IDH']
        result += Byte(self.bits)
        modulo  = (1<<self.bits)-2
        blocks  = ""
        block   = ""
        for i, datum in enumerate(data):
            if not (i%modulo):
                block += self.clear
                blocks += Byte(len(block))
                blocks += block
                block   = ""
            if isinstance(datum, int):
                assert 0 <= datum <= 255
                block += Byte(datum)
            else:
                block += datum
        if len(block) != 0:
            blocks += Byte(len(block))
            blocks += block
        blocks += self.eoi
        result += blocks+Byte(0)
        return result

    def save(self, name):
        data = ""
        for label in ['INIT', 'LSD', 'GCT', 'EXT']:
            data += self[label]
        # Frames must sort as in: 01 02 03 04 05 06 07 08 09 10 11 12
        for label in [key for key in sorted(self.keys()) if key.isdigit()]:
            #print label
            data += self[label]
        for label in ['FINI',]:
            data += self[label]
        with open(name, 'wb') as target:
            target.write(data)

if __name__ == "__main__":
    X, Y = 100, 100
    fig = Fig(X,Y)
    fig['000'] = fig.frame('0'*(X*Y))
    fig['001'] = fig.frame('1'*(X*Y))
    fig['002'] = fig.frame('2'*(X*Y))
    fig['003'] = fig.frame('3'*(X*Y))
    fig['004'] = fig.frame('4'*(X*Y))
    fig['005'] = fig.frame('5'*(X*Y))
    fig['006'] = fig.frame('6'*(X*Y))
    fig['007'] = fig.frame('7'*(X*Y))
    fig.save('fig.gif')
