# Basic scan

import numpy as np
import http.client
import subprocess
import shutil
import fabric 
import json
import time
import sys
import os

# Scan parameters
mm_per_s = 50 # Print head speed
settle_s = 5 # Settling time before image capture

z_max = 100 # z jog limits (void collision)
z_min = 71 
xc = 100 # X center
yc = 100 # Y center

sweep_w = 70
sweep_h = 70
vx = np.linspace(xc-sweep_w/2, xc+sweep_w/2, 8)
vy = np.linspace(yc-sweep_h/2, yc+sweep_h/2, 8)
if len(sys.argv) > 1: z = float(sys.argv[1]) # Take the z height (mm) from the first CLI arg
else: z = z_min
n_img = len(vx)*len(vy)

# Exposure parameters
shutter_us = int(100e-3*1e6)
gain = 1.0
awb_red = 2.0
awb_blue = 2.0
denoise = 'off'
enc = 'bmp'

# Connection and directory options
n_max_dl = 1 # Max number of concurrent downloads from rpi 
local_outdir = '.\\scan' # Where to save the images coming from the rpi
hostuser = 'user' # rpi username
hostname = 'raspbian.local' # rpi network location
op_port = 5000 # port rpi's octoprint listens on
op_key = '3250085121E3424B93998369A46FEA7D' # OctoPrint api key for hostuser
rpi_outdir = '~/scan' # Directory to save images on the rpi

# Command definition
rpi_cmd_capture = f'libcamera-still --shutter {shutter_us} --gain {gain} --awbgains {awb_red},{awb_blue} --denoise {denoise} -e {enc} --immediate -n -o'
op_post_path = '/api/printer/printhead'
op_header = {
    'Content-type': 'application/json',
    'Authorization': f'Bearer {op_key}',
    }
op_cmd_jog = {
    'command': 'jog', 
    'absolute': True,
    'y': [],
    'z': [],
    'speed': mm_per_s*60, 
    }

def jog(x,y,z): # Jog printhead
    op_cmd_jog.update({
        'x': x, 
        'y': y, 
        'z': min(z_max, max(z_min, z)),
        }) 
    op_json_cmd_jog = json.dumps(op_cmd_jog)
    op_conn.request('POST', op_post_path, op_json_cmd_jog, op_header) 
    resp = op_conn.getresponse().read()
    return resp

# Clean up and establish connections to rpi
if os.path.exists(local_outdir): shutil.rmtree(local_outdir) # Make or clear out local directory
os.makedirs(local_outdir, exist_ok=True)
ssh_conn = fabric.Connection(hostname, hostuser) # Connect to rpi
ssh_conn.run(f'mkdir -p {rpi_outdir}; rm -rf {rpi_outdir}/*') # Make or clear out rpi directory
op_conn = http.client.HTTPConnection(hostname, op_port) # Connect to rpi OctoPrint

# Download management subroutines
l_to_dl = [] # List of download commands that still need to be executed
l_dl = [] # List of started download processes

def count_active_dl(): # Count the active downloads in l_dl 
    n_alive = 0
    for p in l_dl: 
        if p.poll() is None: n_alive += 1
    return n_alive

def manage_dl(): # Start downloads in l_to_dl (if possible), return 0 when everything is done
    n_active = count_active_dl() 
    n_to_start = min(len(l_to_dl), n_max_dl-n_active)
    for idl in range(n_to_start): 
        cmd = l_to_dl.pop(0) # FIFO
        p = subprocess.Popen(cmd)
        l_dl += [p]
        print(f'\nDownloading segment {len(l_dl)} of {n_img}')
    if (n_active == 0) and (len(l_dl) == n_img): return 0
    else: return 1

# Capture loop
t0 = time.time()
vix = list(range(len(vx)))
viy = list(range(len(vy)))
absidx = 0

r = jog(vx[0], vy[-1], z) # The first jog may be a longer sweep, so go there ahead of the loop & sleep extra
time.sleep(settle_s) 
for ix in vix:
    viy = np.flip(viy) # Zig-zag to jog less
    x = vx[ix]
    for iy in viy:
        y = vy[iy]
        absidx += 1
        fname = f'{rpi_outdir}/img_r{iy:03d}_c{ix:03d}.{enc}' 
        print(f'\nCapturing {fname} ({absidx} of {n_img})')

        r = jog(x,y,z)
        print(r.decode())

        time.sleep(settle_s) # Settle and capture
        ssh_conn.run(f'{rpi_cmd_capture} {fname}')

        # Queue the segment for retreival
        l_to_dl += [['scp', '-r', f'{hostuser}@{hostname}:{fname}', local_outdir]]
        manage_dl() # Start new downloads if possible

# Finish
jog(xc, yc, z_min) # Return to 0
ssh_conn.close()
op_conn.close()
while manage_dl(): time.sleep(1.0) # Wait for downloads to complete

print(f'\n{time.time()-t0:.2f} s\n')
