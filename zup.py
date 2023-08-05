# Pull head to around the middle of the volume

import http.client
import json

mm_per_s = 50 # Print head speed
z_max = 100 # z jog limits (void collision)
z_min = 71 
xc = 80 # X center
yc = 100 # Y center

x = xc
y = yc
z = z_min

hostuser = 'user' # rpi username
hostname = 'raspbian.local' # rpi network location
op_port = 5000 # port rpi's octoprint listens on
op_key = '3250085121E3424B93998369A46FEA7D' # OctoPrint api key for hostuser

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

op_conn = http.client.HTTPConnection(hostname, op_port) # Connect to rpi OctoPrint
def jog(x,y,z): # Jog printhead
    op_cmd_jog.update({
        'x': x, 
        'y': y, 
        'z': min(z_max, max(z_min, z))
        }) 
    op_json_cmd_jog = json.dumps(op_cmd_jog)
    op_conn.request('POST', op_post_path, op_json_cmd_jog, op_header) 
    resp = op_conn.getresponse()
    return resp

jog(xc,yc,z_min) # Return to 0
op_conn.close()
