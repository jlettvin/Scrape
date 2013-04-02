#!/usr/bin/env python

from fabricate import *

sources = ['program', 'util']

def build():
    compile()
    link()

def compile():
    for source in sources:
        run('gcc', '-c', source+'.c')

def link():
    objects = [s+'.o' for s in sources]
    run('gcc', '-o', 'program', objects)

def clean():
    autoclean()

main()
