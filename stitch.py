# Attempt to merge a basic scan 

# Expects scandir to be populated by basic_scan (filenames like r###_c###.bmp)
# - Finds control points for each group of 2x2 adjacent images
#   (You can stitch a sub-rectangle instead by designing your own vr, vc)
# - Globs all the found control points into a new, big project file
# - Stitches the big project file
# 
# This approach avoids panotools wasting cycles searching for impossible 
# control points.

import numpy as np

import os
import sys
import shutil
import subprocess
import glob
import time

# Stitch options
nr = 3
nc = 3
vr = range(nr-1) # Rows to loop over (north sub-grid)
vc = range(nc-1) # Cols to loop over (west sub-grid)
n_groups = len(vr)*len(vc)
n_img = (len(vr)+1)*(len(vc)+1)

ptopt = 'y,p,r' # autooptimiser parameters for panotools to optimize
ptset = 'v=1.0' # autooptimiser parameters for panotools to set

# Directories and filenames
enc = 'bmp'
scandir = './scan' # Where the scan images are
stitchdir = './stitch_files' # Directory for stitch project files
outname = './stitch.tif' # Full stitch output
ptpath = 'C:/Program Files/Hugin/bin' # Location of panotools binaries

# Clean up
if os.path.exists(stitchdir): shutil.rmtree(stitchdir) # Make or clear out stitch directory
os.makedirs(stitchdir, exist_ok=True)

# Find control points on each 2x2 grid of adjacent images
t0 = time.time()
absidx = 0
l_fcp = []
for r in vr: 
    for c in vc:
        absidx += 1
        fcp = f'{stitchdir}/r{r}_c{c}.pto'  
        print(f'Making control points {fcp} ({absidx} of {n_groups})')

        fnw = f'{scandir}/r{r+0}_c{c+0}.{enc}' 
        fne = f'{scandir}/r{r+0}_c{c+1}.{enc}' 
        fsw = f'{scandir}/r{r+1}_c{c+0}.{enc}' 
        fse = f'{scandir}/r{r+1}_c{c+1}.{enc}' 

        subprocess.Popen( # Make a project file with these images
                [f'{ptpath}/pto_gen', f'-o{fcp}', fnw, fne, fsw, fse],
                stdout=subprocess.STDOUT, stderr=subprocess.STDOUT).wait()
        subprocess.Popen( # Find control points 
                [f'{ptpath}/cpfind', f'-o{fcp}', fcp],
                stdout=subprocess.STDOUT, stderr=subprocess.STDOUT).wait()

        l_fcp.append(fcp)

print(f'Positioning segments using all control points.')
fstitch = f'{stitchdir}/stitch.pto'
subprocess.Popen( # Merge project files from the grid loop
        [f'{ptpath}/pto_merge', f'-o{fstitch}'] + l_fcp,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()
subprocess.Popen( # Remove duplicates/bad control points
        [f'{ptpath}/cpclean', f'-o{fstitch}', fstitch],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()
subprocess.Popen( # Specify the optimiztion to be performed
        [f'{ptpath}/pto_var', f'--opt={ptopt}', f'--set={ptset}', f'-o{fstitch}', fstitch],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()
subprocess.Popen( # Execute position optimization
        [f'{ptpath}/autooptimiser', '-n', f'-o{fstitch}', fstitch],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()

subprocess.Popen( # Design output canvas
        [f'{ptpath}/pano_modify', '--canvas=AUTO', '--crop=AUTO', f'-o{fstitch}', fstitch],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()

for idxi in range(n_img): # Remap all the segments 
    print(f'Remapping segment {idxi+1} of {n_img}')
    subprocess.Popen( 
            [f'{ptpath}/nona', f'-i={idxi}', '-mTIFF_m', f'-o{stitchdir}/stitch_', fstitch],
            ).wait()
print(f'Creating stitch.')
l_remap = glob.glob(f'{stitchdir}/stitch_*.tif') # Get all the remapped images
subprocess.Popen( # Blend seams in the final output
        [f'{ptpath}/enblend', f'-o{outname}'] + l_remap,
        ).wait()

print(f'{time.time()-t0} s')
