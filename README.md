# Ender Scanner
## Tools for scanning film negatives with an Ender 3 Neo

A Raspberry Pi HD camera can be mounted face-down on the printhead of an Ender 3 3D printer and swept around to capture 2D scans of the print plane.
The Ender 3's print volume is big enough to fit a light panel and loaded film negative holder. 
This setup involves several ingredients (roughly in order of build and usage steps):
 
 - `ender3_picamera_v2.scad`: A bracket to mount he Raspberry Pi HD camera on the print head with M5 nuts. 
	This is a pretty early design.
	- To reduce vibration, the Ender 3's printhead also needs to be modded with a switch to turn the front fan off.
 - The Raspberry Pi HD camera I am using for development is the commonly available 16 mm C-mount lens, plus an extra 5 mm macro extension (in addition to the 5 mm "CS-to-C" extension that comes with the HD camera module). 
 - A Raspberry Pi Zero W operates the camera, and the Ender 3 printhead via OctoPrint. 
	A separate 'host computer' is going to operate the camera and Ender 3 through this Zero W:
	- The Zero W has SSH access with no-password pubkey authentication. The host uses this interface to capture images & download them.
	- OctoPrint has a web interface with a REST API key for the main OctoPrint user. The host uses this interface to control the print head.
 - A bunch of scripts to run on the host computer that perform scan functions:
	- `zup.py`: Draw the print head up to a "center" location + some Z displacement.
		After running this, roughly center the light panel + film negative underneath the camera. 
	- `zstack.py`: Capture a bunch of images of the film negative for a range of Z displacements, and download them to a folder on the host computer. 
		This is used to find the focus plane. 
	- `basic_scan.py`: Sweep the print head around to capture an X-Y grid of images, and download them to a folder on the host computer.
	- `correct_metadata.py`: Bitmaps produced by the Raspberry Pi Camera have a negative y dimension, seemingly to represent that they should be mirrored.
		Panotools will refuse to process the images because of this. 
		This script refreshes the data to positive dimensions and actually performs the mirroring.
	- (TODO) `merge.py`: Attempts to merge partial image captures from `basic_scan.py` using panotools. 
		The strategy: get control points for each group of 2x2 in the grid. 
		Make a new project file with all the control points, and find optimal positions.

