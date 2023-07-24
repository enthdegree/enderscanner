## Attempt to merge a basic scan 
#
# - Finds control points for each group of 2x2 adjacent images
#   (You can stitch a sub-rectangle instead by designing your own vr, vc)
# - Globs all the found control points into a new, big project file
# - Stitches the big project file
#
# This approach prevents panotools from wasting cycles on bad control points.
#
# At runtime, the script expects scandir to be populated by files collected 
# by basic_scan.py (with filenames like r###_c###.bmp)
#
# Aside from the imported modules, this script depends on:
#  - ptpath: path to Panotools binaries, for example the ones included in a 
#    Hugin installation
#  - cmd_blend: A blend tool like Panotools' enblend. enblend is slow for large
#    stitches, but can be enabled if you still want it.
#    Multiblend seems to work impressively well: https://horman.net/multiblend/ 
# 
 

import numpy as np

import os
import sys
import shutil
import subprocess
import threading
import glob
import time
from PIL import Image, ImageOps

# Runtime options
n_max_threads = 3 # Max # of threads to 
verbose = False 

# Directories and filenames
enc = 'bmp'
scandir = './scan' # Where the scan images are
stitchdir = './stitch_files' # Directory for stitch project files
outname = './stitch.tif' # Full stitch output
ptpath = 'C:/Program Files/Hugin/bin' # Location of panotools binaries

# Stitch options
nr = 10
nc = 10
vr = range(nr-1) # Rows to loop over (north sub-grid)
vc = range(nc-1) # Cols to loop over (west sub-grid)
n_groups = len(vr)*len(vc)
n_img = (len(vr)+1)*(len(vc)+1)
truemirror = False # See below, 'Correct libcamera-still header'

ptopt = 'y,p,r,v,b' # autooptimiser parameters for panotools to optimize
ptset = 'v=1.0' # autooptimiser parameters for panotools to set
cmd_blend = './multiblend/multiblend' # Multiblend: https://horman.net/multiblend/
#cmd_blend = f'{ptpath}/enblend # panotools' enblend (slow)

# Clean up
print('Cleaning up.')
if os.path.exists(stitchdir): shutil.rmtree(stitchdir) # Make or clear out stitch directory
os.makedirs(stitchdir, exist_ok=True)

# Correct libcamera-still header
# libcamera-still produces images with negative height, which panotools rejects
# Presumably this is done to represent that the image data should be mirrored. 
# This rewrites dimensions to positive and rearranges the image data if truemirror is True
print('Rewriting bitmap headers.')
for fname in glob.glob(f'{scandir}/*.{enc}'):
    im = Image.open(fname)
    if truemirror: im = ImageOps.mirror(im)
    im.save(fname)

outstream = subprocess.STDOUT
if not verbose: 
    outstream = subprocess.DEVNULL

# Find control points on each 2x2 grid of adjacent images
t0 = time.time()
absidx = 0
l_cp = [] # List of control point files
l_cmd = [] # List of command lists to run to find control points
l_t = [] # List of threads that get spawned 
for r in vr: # Get the list of commands to execute
    for c in vc:
        absidx += 1
        cp = f'{stitchdir}/r{r:03d}_c{c:03d}.pto'  
        l_cp.append(cp)
        lq = [
            f'{scandir}/r{r+0:03d}_c{c+0:03d}.{enc}', 
            f'{scandir}/r{r+0:03d}_c{c+1:03d}.{enc}', 
            f'{scandir}/r{r+1:03d}_c{c+0:03d}.{enc}', 
            f'{scandir}/r{r+1:03d}_c{c+1:03d}.{enc}', 
            ]
        cmd = {
            'absidx': absidx, 
            'makeproject': [f'{ptpath}/pto_gen', f'--output={cp}'] + lq,
            'findcp': [f'{ptpath}/cpfind', f'--output={cp}', cp], 
            }
        l_cmd.append(cmd)

# Run all of l_cmd in as many threads as allowed 
def cp_worker(cmd):
    absidx = cmd['absidx']
    cp = l_cp[absidx-1]
    print(f'Making control points {cp} ({absidx} of {n_groups}).')
    subprocess.Popen(cmd['makeproject'], stdout=outstream).wait()
    subprocess.Popen(cmd['findcp'], stdout=outstream).wait()
    return
for cmd in l_cmd:
    is_started = False
    while not is_started:
        if threading.active_count() < n_max_threads:
            t = threading.Thread(target=cp_worker, args=(cmd,))
            t.start()
            l_t.append(t)
            is_started = True
        else: time.sleep(1.0)
for t in l_t: t.join() # Finish up

fstitch = f'{stitchdir}/stitch.pto'
print(f'Positioning segments using all control points.')
subprocess.Popen( # Merge project files from the grid loop
        [f'{ptpath}/pto_merge', f'--output={fstitch}'] + l_cp,
        stdout=outstream).wait()
subprocess.Popen( # Remove duplicates/bad control points
        [f'{ptpath}/cpclean', f'--output={fstitch}', fstitch],
        stdout=outstream).wait()
subprocess.Popen( # Specify the optimiztion to be performed
        [f'{ptpath}/pto_var', f'--opt={ptopt}', f'--set={ptset}', f'--output={fstitch}', fstitch],
        stdout=outstream).wait()
subprocess.Popen( # Execute position optimization
        [f'{ptpath}/autooptimiser', '-n', f'--output={fstitch}', fstitch],
        stdout=outstream).wait()
subprocess.Popen( # Design output canvas
        [f'{ptpath}/pano_modify', '--fov=AUTO', '--center', '--canvas=AUTO', f'--output={fstitch}', fstitch],
        stdout=outstream).wait()

print(f'Remapping segments')
subprocess.Popen( 
        [f'{ptpath}/nona', '-m', 'TIFF_m', '-v', f'--output={stitchdir}/stitch_', fstitch],
        ).wait()

print(f'Creating stitch.')
l_remap = glob.glob(f'{stitchdir}/stitch_*.tif') # Get all the remapped images
subprocess.Popen( # Blend seams in the final output
        [cmd_blend, f'--output={outname}'] + l_remap,
        ).wait()

print(f'{time.time()-t0} s')
