#!/usr/bin/env python

"""
browsISO.py implements a browser for ISO files as if they were disks.
Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__date__       = "20110311"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"

import sys, termios, atexit
from select import select

class Raw(object):
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.org = termios.tcgetattr(self.fd)
        self.raw = termios.tcgetattr(self.fd)
        self.raw[3] = (self.raw[3] & ~termios.ICANON & ~termios.ECHO)
        atexit.register(self.set_normal_term)
    def set_normal_term(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.org)
    def set_curses_term(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.raw)
    def putch(self, ch): sys.stdout.write(ch)
    def getch(self): return sys.stdin.read(1)
    def getche(self): ch = getch(); putch(ch); return ch
    def kbhit(self): dr,dw,de = select([sys.stdin], [], [], 0); return dr <> []
    def __enter__(self): self.set_curses_term(); return self
    def __exit__(self, type, value, traceback): self.set_normal_term()

if __name__ == "__main__":
    try:
        with Raw() as raw:
            number = 0
            while not raw.kbhit():
                print number, '\r',
                number += 1
    except Exception, e:
        print e, "\nexcept:", sys.exc_info()[0], sys.exc_info()[1]
