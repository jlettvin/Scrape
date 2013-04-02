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
#from bitstring import *

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
    print N
    assert isinstance(N, int)
    assert 0 <= N <= 65535
    return pack("H", N)

def Bytes(Ns):
    assert isinstance(Ns, list)
    result = ""
    for N in Ns:
        result += Byte(N)
    return result

#def block(s):
    #return Byte(len(s)+1) + "\x01" + s + Byte(0)

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
        self['EXT']     = self.application()
        self['GCE']     = self.graphics(UByte(gval)+delay+trans)
        self['IDH']     = sep+Word(Left)+Word(Top)+self['XY']+self.tail

        self['FINI']    = exit

    def graphics(self, data):
        return self.head+Byte(0xf9)+Byte(len(data))+data+Byte(0)

    def application(self, vendor="NETSCAPE2.0", rpt="\x00\x00"):
        result  = self.head+self.app        # 0, 1
        result += Byte(len(vendor))+vendor  # 2, 3-13
        result += Byte(len(rpt)+1)+"\x01"+rpt
        #result += block(rpt)                # 14, 15, 16, 17
        result += self.tail                 # 18
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
        print "\\x%02x\\x%02x" % (x,y)
        result += self.application("XYOFFSET", "\\x%02x\\x%02x" % (x,y))
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

    def showHEX  (self, data):
        print ":".join("{0:x}".format(ord(b)) for b in data)
    def showINIT (self):
        print ' INIT:', self['INIT']
    def showLSD  (self):
        print '  LSD:' ,
        data = unpack("HHBBB", self['LSD'])
        pval = data[2]
        gctf = (pval >> 7) & 1
        res  = (pval >> 4) & 7
        sort = (pval >> 3) & 1
        cts  = (pval >> 0) & 7
        print "X:%d Y:%d pval:%d %d %d" % data,
        print "\tgctf:%d, res:%d, sort:%d, cts:%d" % (gctf, res, sort, cts)
    def showGCT  (self):
        #print len(self['EXT'])
        #data = unpack("BBBBBBHBB", self['EXT'])
        #gval = data[0]
        #rsv  = (gval >> 6) & 7
        #disp = (gval >> 3) & 7
        #inp  = (gval >> 1) & 1
        #tcf  = (gval >> 0) & 1
        print '  GCT:' ,
        print len(self['GCT']) / 3, ' triples'
        #self.showHEX(self['GCT' ])
    def showEXT  (self):
        raw = self['EXT']
        vendor = raw[3:14]
        print vendor, len(raw)
        ##                 NETSCAPE2.0
        data = unpack("bbbbbbbbbbbbbbbbHb", raw)
        bsz  = int(data[14])
        a    = data[15]
        trm  = data[16]
        print '  EXT:' , vendor,
        print 'bsz:%d, a:%d, trm:%d' % (bsz,a,trm),
        self.showHEX(raw)
    def showFINI (self):
        print ' FINI:',
        self.showHEX(self['FINI'])
    def showFRAME(self, number):
        print 'FRAME:', number

    def show(self, label):
        if   label == 'INIT':   self.showINIT (     )
        elif label ==  'LSD':   self.showLSD  (     )
        elif label ==  'GCT':   self.showGCT  (     )
        elif label ==  'EXT':   self.showEXT  (     )
        elif label == 'FINI':   self.showFINI (     )
        else:                   self.showFRAME(label)

    def save(self, name):
        data = ""
        for label in ['INIT', 'LSD', 'GCT', 'EXT']:
            self.show(label)
            data += self[label]
        # Frames must sort as in: 01 02 03 04 05 06 07 08 09 10 11 12
        for label in [key for key in sorted(self.keys()) if key.isdigit()]:
            #print label
            self.show(label)
            data += self[label]
        for label in ['FINI',]:
            self.show(label)
            data += self[label]
        with open(name, 'wb') as target:
            target.write(data)

if __name__ == "__main__":
    X, Y = 100, 100
    fig = Fig(X,Y)
    fig['000'] = fig.frame('A'*(X*Y))
    fig['001'] = fig.frame('B'*(X*Y))
    fig['002'] = fig.frame('C'*(X*Y))
    fig['003'] = fig.frame('D'*(X*Y))
    fig['004'] = fig.frame('E'*(X*Y))
    fig['005'] = fig.frame('F'*(X*Y))
    fig['006'] = fig.frame('G'*(X*Y))
    fig['007'] = fig.frame('H'*(X*Y))
    fig.save('fig.gif')
