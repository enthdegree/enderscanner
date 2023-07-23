// Mount a downward-facing Raspberry Pi HD camera on an Ender 3 print head
$fa = 1; 
$fs = 0.1;

// Dimensions
dilate = 1; // How much should hole diameters be expanded?

faceplate_bolt_diam = 5; // The mounting bolts are M5
faceplate_nut_diam = 8/cos(30);
faceplate_sep = 37.5; // Separation between the centers of the two wheels that roll along the X axis 
faceplate_nut_countersink = 3;
faceplate_extra_thickness = 1; // How thick should material be past the mount bolt countersink? (n.b. we only have 3mm of exposed mounting bolt thread to work with)
faceplate_shoulder = 3;
faceplate_total_depth = 2*faceplate_shoulder + 9;
faceplate_total_height = faceplate_extra_thickness + faceplate_nut_countersink;

printhead_back_height = 23; // Back of the print head's distance from zero
printhead_top_depth = 11.5; // (real-life-)z displacement to get from 0 to the top of the print head

camera_bolt_diam = 6.35; // The camera screw is a 1/4"-20
camera_bolt_height = 68; // How far (real-life-)forward from zero should the camera mount beam go?
camera_bolt_offset = 36; // How far to the (real-life-)right from zero is the camera bolt?
camera_bolt_depth = 11; // (real-life-)z displacement to get from 0 to the camera bolt center

// Faceplate definition
module faceplate_body() {
    translate([-dilate/2, -faceplate_total_depth/2, -faceplate_total_height/2]) {
         cube([(faceplate_sep+dilate)/2, faceplate_total_depth, faceplate_total_height]);
    }
    translate([faceplate_sep/2,0,-faceplate_total_height/2]) {
        cylinder(h=faceplate_total_height, d=faceplate_total_depth);
    }
};

module faceplate_holes() {
    // Mounting bolt screw hole
    translate([faceplate_sep/2, 0, 0]) {
        cylinder(h=faceplate_total_height+dilate, d=faceplate_bolt_diam+dilate,
        center=true);
    }

    // Mounting bolt countersink
    translate([faceplate_sep/2, 0, (+faceplate_total_height-faceplate_nut_countersink+dilate)/2]) {
        cylinder(h=faceplate_nut_countersink+dilate, 
            d1=faceplate_nut_diam,
            d2=faceplate_nut_diam+2*dilate,
            center=true);
    }
};

module half_faceplate_body() {
    difference() { 
        faceplate_body(); 
        faceplate_holes();
    }
};

module mount() {
    union() {
        half_faceplate_body();
        mirror([1,0,0]) half_faceplate_body();
    }
};

beam_width = faceplate_total_depth;
beam_thickness = faceplate_total_height;
camera_bolt_pt = [camera_bolt_offset, camera_bolt_depth, camera_bolt_height];

// Beam definition
module beam_body() {
    
    /*
    translate([0, camera_bolt_depth, camera_bolt_height/2]) cube(2,center=true);
    translate([0, camera_bolt_depth, camera_bolt_height/1]) cube(2,center=true);
    translate([camera_bolt_offset, camera_bolt_depth, camera_bolt_height/2]) cube(2,center=true);
    translate([camera_bolt_offset, camera_bolt_depth, camera_bolt_height/1]) cube(2,center=true);
    */
    
    // Beam from zero to top of printhead (depth extension)
    beam_0_ext = [0,printhead_top_depth,0];
    beam_0_overshoot = [0,beam_thickness,0];
    beam_0_dims = [beam_width, 0, beam_thickness] + beam_0_ext + beam_0_overshoot; 
    beam_0_c = (beam_0_ext+beam_0_overshoot)/2;
    translate(beam_0_c) cube(beam_0_dims, center=true);
    
    // From beam 0 to past print head coasters (height extension)
    beam_1_ext = [0,0,camera_bolt_height/2-beam_width];
    beam_1_overshoot = [0,0,beam_width];
    beam_1_dims = [beam_width, beam_thickness, 0] + beam_1_ext + beam_1_overshoot;
    beam_1_c = beam_0_c + beam_0_ext/2 + (beam_1_ext+beam_1_overshoot)/2;
    translate(beam_1_c) cube(beam_1_dims, center=true);

    // From beam 1 to right edge of print head (width extension)
    beam_2_ext = [camera_bolt_offset/4,0,0];
    beam_2_overshoot = [beam_width,0,0];
    beam_2_dims = [0, beam_thickness, beam_width] + beam_2_ext + beam_2_overshoot;
    beam_2_c = beam_1_c + beam_1_ext/2 + (beam_2_ext+beam_2_overshoot)/2;
    translate(beam_2_c) cube(beam_2_dims, center=true);

    // From beam 2 to bolt front (height extension)
    beam_3_ext = [0,0,camera_bolt_height/2+beam_width/2-beam_thickness];
    beam_3_overshoot = [0,0,beam_thickness];
    beam_3_dims = [beam_width, beam_thickness, 0] + beam_3_ext + beam_3_overshoot;
    beam_3_c = beam_2_c + beam_2_ext/2 + (beam_3_ext+beam_3_overshoot)/2;
    translate(beam_3_c) cube(beam_3_dims, center=true);                    
    // From beam 3 to bolt front (width extension)
    beam_4_ext = [beam_width,0,0];
    beam_4_overshoot = [0,0,0]; 
    beam_4_dims = [0, beam_thickness, beam_thickness] + beam_4_ext + beam_4_overshoot;
    beam_4_c = beam_3_c + beam_3_ext/2 + (beam_4_ext+beam_4_overshoot)/2 + [beam_width/2-beam_thickness,0,0];
    translate(beam_4_c) cube(beam_4_dims, center=true);
    
    translate(camera_bolt_pt-[0,0,beam_thickness/2])
    cylinder(h=beam_thickness, r=camera_bolt_diam+2*faceplate_shoulder/2-dilate/2, center=true);
    
    translate(camera_bolt_pt-[11,-3,beam_thickness/2])
    cylinder(h=beam_thickness, r=5, center=true);
}

module camera_bolt_hole() {
    translate(camera_bolt_pt)
    cylinder(h=beam_width,
        d=camera_bolt_diam + dilate, 
        center=true); 
}

module beam() {
    difference() {
        beam_body();
        camera_bolt_hole();
    }
}

union() {
    mount();
    beam();
}
