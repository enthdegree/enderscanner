# Get a z stack

import numpy as np
import http.client
import subprocess
import fabric 
import shutil
import json
import time
import sys
import os

# Scan parameters
mm_per_s = 50 # Print head speed
settle_s = 10 # Settling time before image capture

z_max = 250 # z jog limits (void collision)
z_min = 100 
xc = 80 # X center
yc = 95 # Y center

if len(sys.argv) > 1: zstart = float(sys.argv[1]) 
else: zstart = z_min
if len(sys.argv) > 2: zend = float(sys.argv[2]) 
else: zend = z_min+10

x = xc
y = yc
vz = np.linspace(zstart, zend, 10)

# Exposure parameters
shutter_us = int(10e-3*1e6)
gain = 1.0
awb_red = 2.2
awb_blue = 1.3
denoise = 'off'

# Connection and directory options
local_outdir = './zstack' # Where to save the images coming from the rpi
hostuser = 'user' # rpi username
hostname = 'raspbian.local' # rpi network location
op_port = 5000 # port rpi's octoprint listens on
op_key = '3250085121E3424B93998369A46FEA7D' # OctoPrint api key for hostuser
rpi_outdir = '~/scan' # Directory to save images on the rpi
enc = 'jpg'

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

def jog(x,y,z=z_min): # Jog printhead
    op_cmd_jog.update({
        'x': x, 
        'y': y, 
        'z': min(z_max, max(z_min, z))
        }) 
    op_json_cmd_jog = json.dumps(op_cmd_jog)
    op_conn.request('POST', op_post_path, op_json_cmd_jog, op_header) 
    resp = op_conn.getresponse()
    print(resp.read().decode())
    return 

# Setup
if os.path.exists(local_outdir): shutil.rmtree(local_outdir) # Make or clear out local directory
os.makedirs(local_outdir, exist_ok=True)

ssh_conn = fabric.Connection(hostname, hostuser) # Connect to rpi
ssh_conn.run(f'mkdir -p {rpi_outdir}; rm -rf {rpi_outdir}/*') # Make or clear out rpi directory
op_conn = http.client.HTTPConnection(hostname, op_port) # Connect to rpi OctoPrint

# Capture loop
t0 = time.time()
r = jog(x, y, vz[0])
time.sleep(settle_s) # Settle longer for the first jog
l_dl = []
for z in vz:
    fname = f'{rpi_outdir}/z{z:.2f}.{enc}' 
    print(f'Capturing {fname}')

    r = jog(x,y,z)
    time.sleep(settle_s) # Settle and capture
    ssh_conn.run(f'{rpi_cmd_capture} {fname}')

    # Retreive segment
    p = subprocess.Popen(['scp', '-r', f'{hostuser}@{hostname}:{fname}', local_outdir])
    l_dl.append(p)

jog(xc,yc,z_min) # Return to 0

# Finish
for p in l_dl: p.wait() # Wait for downloads to complete
ssh_conn.close()
op_conn.close()

print(f'\n{time.time()-t0:.2f} s\n')
