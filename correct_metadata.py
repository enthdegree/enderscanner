# Correct the metadata from RPi HD Camera bmps out of libcamera-still (by opening and rewriting it)
# libcamera-still produces images with negative dimension which some merge tools reject

import sys
import glob
from PIL import Image, ImageOps

if len(sys.argv) > 1: scandir = 'scan'
else: scandir = sys.argv[1]

for fname in glob.glob(f'{scandir}/*.bmp'):
    im = Image.open(fname)
    im = ImageOps.mirror(im)
    im.save(fname)

