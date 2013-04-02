#!/usr/bin/env python

###############################################################################
__date__       = "20130301"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"
__version__    = "0.0.1"

"""
xlog.py

Implementes cut/paste buffer capture listener for linux.

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

See __main__ for an example of use.
"""

import pygtk, gtk, time

clips = [""]

clipboard = gtk.clipboard_get()

while True:
    clip = clipboard.wait_for_text()
    if clip != clips[-1]:
        clips += [clip,]
        print clip
        with open('clipfile', 'a+') as clipfile:
            print>>clipfile, clip
