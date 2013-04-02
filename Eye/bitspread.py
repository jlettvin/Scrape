#!/usr/bin/env python

import sys

def bits(x): return bin(int(x))[2:]

if len(sys.argv) > 1:
    #spread = 1
    target = '100100100'
    #print target
    value = sys.argv[1]
    for spread in range(1, 445):
        print value, spread
        if target == bits(value*spread):
            print spread
    #print bits(value), bits(value*spread)
