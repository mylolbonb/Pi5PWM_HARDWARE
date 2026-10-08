// =====================================================================
//  Two-stage C6 FPV rocket  -  fully 3D printed
//  Camera: Walksnail Ascent Lite kit (VTX 30.5x30.5x3.5, cam 12x14x15)
//
//  Layout (single airframe, "motor-eject" staging):
//    - Minimum-diameter body: the body IS the 18 mm motor tube.
//    - Booster C6-0 sits at the very back, butted nozzle-to-nozzle...
//      (C6-0 top against the C6-5/C6-7 nozzle) with ONE wrap of tape.
//    - When the C6-0 burns through it lights the sustainer and the
//      spent booster casing is blown out the back. Nothing else drops.
//    - The sustainer is stopped by a printed thrust ring.
//    - Hammerhead FPV payload: VTX board stands vertically in a wider
//      bay, battery beside it.
//    - Camera sits in a side pod at the base of the nose and looks DOWN
//      along the body (sees the fins and the ground falling away).
//    - At apogee the sustainer ejection charge pushes the whole front
//      (payload bay + nose, glued together) off the body; it stays tied
//      to the body with kevlar and comes down on a streamer.
//
//  Select what to render/export with `part`.
// =====================================================================

part = "assembly"; // [assembly, section, body, payload, nose, all_print]

/* [Quality] */
$fn = 96;

/* [Motors - Estes C6 (18 x 70 mm)] */
motor_d        = 18.0;
motor_len      = 70.0;
motor_clear    = 0.4;    // diametral clearance for the printed bore
n_motors       = 2;      // booster + sustainer stacked in the tube

/* [Body] */
wall           = 1.5;    // body wall
thrust_ring_h  = 2.0;
thrust_ring_id = 13.0;   // ejection gas passes through this
bay_len        = 60;     // streamer + wadding bay above the thrust ring

/* [Fins] */
n_fins         = 3;
fin_root       = 55;
fin_tip        = 20;
fin_span       = 34;
fin_le_sweep   = 28;     // leading edge sweep (along body axis)
fin_t          = 1.6;

/* [Launch lug - 1/8 in rod] */
lug_id         = 3.8;
lug_wall       = 0.8;
lug_len        = 40;
lug_z          = 75;     // bottom of lug from aft end

/* [Payload bay] */
pay_wall       = 1.5;
pay_id         = 32.0;   // VTX 30.5 board stands vertically -> needs ~31.5
pay_len        = 44;     // straight section length
trans_len      = 22;     // body -> payload flare
shoulder_len   = 15;     // slides into top of body
shoulder_clear = 0.3;
bulkhead_t     = 1.2;

/* [Walksnail Ascent Lite VTX] */
vtx_w          = 30.5;
vtx_t          = 5.0;    // board 3.5 + parts; slot width
vtx_guide_d    = 2.0;    // how far the guides reach in from the wall

/* [Battery (1S LiPo, VTX takes 3-12.6 V)] */
batt_w         = 18;
batt_t         = 7;
batt_len       = 40;

/* [Switch / charge port] */
port_w         = 6;
port_h         = 10;
port_z         = 20;     // from bottom of straight payload section
vent_d         = 1.5;

/* [Nose + camera] */
nose_len       = 85;     // tangent ogive length
nose_wall      = 1.5;
nose_shoulder  = 10;
tip_round      = 2.0;    // small rounded point
cam_w          = 14.0;   // camera body width  (M2 screw faces, tangential)
cam_h          = 12.0;   // camera body height (radial)
cam_body_len   = 10.0;   // body depth behind the lens
lens_d         = 8.0;    // lens barrel diameter
lens_len       = 5.0;    // lens barrel sticking out of the body front
cam_fit        = 0.3;
cam_screw_back = 5.0;    // M2 side screw: distance behind body front (MEASURE)
cam_screw_d    = 2.3;    // M2 clearance
cam_head_d     = 4.2;    // M2 head counterbore
cam_tilt       = 8;      // lens tilted outward from straight down (deg)
cam_out        = 1.5;    // lens axis this far outside the bay skin
cam_lens_z     = 7;      // height of lens centre above nose base
pod_angle      = 0;      // where the pod sits around the body (0 = over a fin)
pod_wall       = 1.5;
pod_side_wall  = 2.5;    // thicker sides so screw heads sit flush
pod_taper      = 40;     // length of the fairing that blends pod into nose

// ---------------------------------------------------------------- derived
bore      = motor_d + motor_clear;
body_od   = bore + 2*wall;
motor_sec = n_motors*motor_len;
body_len  = motor_sec + thrust_ring_h + bay_len;
pay_od    = pay_id + 2*pay_wall;
nose_R    = pay_od/2;
rho       = (nose_R*nose_R + nose_len*nose_len) / (2*nose_R);
face_r    = tip_round;
nose_cut  = sqrt(rho*rho - pow(face_r - nose_R + rho, 2));
nose_top  = nose_cut + tip_round;
function nose_r(z) = sqrt(rho*rho - z*z) + nose_R - rho;   // ogive radius at height z
eps = 0.01;

echo(str("Body OD = ", body_od, " mm, body length = ", body_len, " mm"));
echo(str("Payload OD = ", pay_od, " mm"));
echo(str("Overall length ~ ", body_len + trans_len + pay_len + nose_top, " mm"));

// ================================================================== BODY
module fin_2d() {
    polygon([
        [0, 0],
        [0, fin_root],
        [fin_span, fin_root - fin_le_sweep],
        [fin_span, fin_root - fin_le_sweep - fin_tip]
    ]);
}

module fin() {
    // fin in XZ plane, root on the body surface
    translate([body_od/2 - 0.6, fin_t/2, 0])
        rotate([90, 0, 0])
            linear_extrude(fin_t) fin_2d();
}

module launch_lug() {
    a = 180/n_fins;   // between fins
    rotate([0, 0, a])
        translate([body_od/2 + lug_id/2 + lug_wall - 0.4, 0, lug_z])
            difference() {
                union() {
                    cylinder(d = lug_id + 2*lug_wall, h = lug_len);
                    // web to body
                    translate([-(lug_id/2 + lug_wall), -1, 0])
                        cube([lug_id/2 + lug_wall, 2, lug_len]);
                }
                translate([0, 0, -1]) cylinder(d = lug_id, h = lug_len + 2);
            }
}

module body() {
    difference() {
        union() {
            cylinder(d = body_od, h = body_len);
            for (i = [0:n_fins-1]) rotate([0, 0, i*360/n_fins]) fin();
            launch_lug();
        }
        // motor bore (both motors)
        translate([0, 0, -1]) cylinder(d = bore, h = motor_sec + 1);
        // gas passage through thrust ring
        cylinder(d = thrust_ring_id, h = body_len);
        // recovery bay
        translate([0, 0, motor_sec + thrust_ring_h])
            cylinder(d = bore, h = bay_len + 1);
        // shock cord tie holes (cross hole through both walls)
        translate([0, 0, body_len - 30])
            rotate([90, 0, 0]) cylinder(d = 2.2, h = body_od + 2, center = true);
        // small chamfer on bore entry
        translate([0, 0, -eps]) cylinder(d1 = bore + 1, d2 = bore, h = 0.8);
    }
}

// =============================================================== PAYLOAD
module vtx_guides() {
    // two guide blocks per side hold the 30.5 board edges, vertical plane = YZ
    for (s = [-1, 1])
        intersection() {
            cylinder(d = pay_id + eps, h = pay_len);
            difference() {
                translate([-(vtx_t/2 + 1.6), s > 0 ? pay_id/2 - vtx_guide_d - 2 : -pay_id/2, 0])
                    cube([vtx_t + 3.2, vtx_guide_d + 2, vtx_w + 2]);
                // slot
                translate([-vtx_t/2, -vtx_w/2, -1]) cube([vtx_t, vtx_w, vtx_w + 4]);
            }
        }
}

module payload() {
    z_tr  = shoulder_len;               // transition start
    z_pay = shoulder_len + trans_len;   // straight section start
    difference() {
        union() {
            // shoulder into body
            cylinder(d = bore - shoulder_clear, h = shoulder_len + eps);
            // flare
            translate([0, 0, z_tr])
                cylinder(d1 = body_od, d2 = pay_od, h = trans_len + eps);
            // straight bay
            translate([0, 0, z_pay]) cylinder(d = pay_od, h = pay_len);
        }
        // hollow shoulder (cord anchor bar is added back later)
        translate([0, 0, -1])
            cylinder(d = bore - shoulder_clear - 2*1.0, h = shoulder_len + 1 - eps);
        // hollow flare above bulkhead
        translate([0, 0, z_tr + bulkhead_t])
            cylinder(d1 = body_od - 2*pay_wall + (pay_od - body_od)*bulkhead_t/trans_len,
                     d2 = pay_id, h = trans_len - bulkhead_t + eps);
        // hollow bay
        translate([0, 0, z_pay]) cylinder(d = pay_id, h = pay_len + 1);
        // switch / charge port (side opposite the VTX slot edges -> +X side)
        translate([pay_od/2 - pay_wall - 1, -port_w/2, z_pay + port_z])
            cube([pay_wall + 2, port_w, port_h]);
        // pressure vent
        translate([0, 0, z_pay + 8])
            rotate([0, 90, 0]) cylinder(d = vent_d, h = pay_od);
    }
    // shock cord bar across the shoulder hollow
    translate([0, 0, 5])
        rotate([90, 0, 0])
            cube([3, 3, bore - shoulder_clear - 1], center = true);
    // VTX guides
    translate([0, 0, z_pay]) vtx_guides();
}

// ================================================================== NOSE
// Tangent ogive with a small rounded point.
module ogive_solid(off = 0) {
    steps = 60;
    pts = [ for (i = [0:steps])
              let(z = nose_cut*i/steps,
                  r = sqrt(rho*rho - z*z) + nose_R - rho)
              [max(r - off, 0.01), z] ];
    rotate_extrude() polygon(concat([[0, 0]], pts, [[0, nose_cut]]));
}

module nose_outer(off = 0) {
    hull() {
        ogive_solid(off);
        translate([0, 0, nose_cut]) sphere(r = max(tip_round - off, 0.3));
    }
}

// Camera frame: origin = centre of camera body front face, local +Z = view
// direction (down, tilted out), local +X = radially inward, local Y = screws.
module cam_frame() {
    lens_x = nose_R + cam_out;
    rotate([0, 0, pod_angle])
        translate([lens_x - lens_len*sin(cam_tilt), 0, cam_lens_z + lens_len*cos(cam_tilt)])
            rotate([0, 180 - cam_tilt, 0])
                children();
}

module pod_envelope() {
    hull() {
        cam_frame()
            translate([-(cam_h/2 + cam_fit/2 + pod_wall), -(cam_w/2 + cam_fit/2 + pod_side_wall),
                       -(cam_body_len + pod_wall)])
                cube([cam_h + cam_fit + 2*pod_wall, cam_w + cam_fit + 2*pod_side_wall,
                      cam_body_len + pod_wall + lens_len]);
        // fairing nose: blends back into the ogive surface
        rotate([0, 0, pod_angle])
            translate([nose_r(cam_lens_z + pod_taper) - 1.5, 0, cam_lens_z + pod_taper])
                sphere(r = 1.5);
    }
}

module nose() {
    difference() {
        union() {
            difference() {
                nose_outer();
                translate([0, 0, -eps]) nose_outer(nose_wall);
            }
            // camera pod (clipped flat at the nose base)
            intersection() {
                pod_envelope();
                cylinder(r = 100, h = 200);
            }
            // base ring tying shell to shoulder
            cylinder(r = nose_R - 0.2, h = nose_wall);
            // shoulder into payload bay
            translate([0, 0, -nose_shoulder])
                cylinder(d = pay_id - shoulder_clear, h = nose_shoulder + eps);
        }
        // camera pocket, open towards the inside of the nose for loading
        cam_frame() {
            translate([-(cam_h + cam_fit)/2, -(cam_w + cam_fit)/2, -cam_body_len - 0.5])
                cube([cam_h + cam_fit + 12, cam_w + cam_fit, cam_body_len + 0.5 + eps]);
            // lens window
            cylinder(d = lens_d + 0.4, h = lens_len + 5);
            // M2 screws, counterbored on both sides
            translate([0, 0, -cam_screw_back]) rotate([90, 0, 0]) {
                cylinder(d = cam_screw_d, h = cam_w + 20, center = true);
                for (s = [-1, 1])
                    translate([0, 0, s > 0 ? cam_w/2 + cam_fit + 1.2 : -(cam_w/2 + 20)])
                        cylinder(d = cam_head_d, h = 20 - 1.2 - cam_fit);
            }
        }
        // hollow shoulder
        translate([0, 0, -nose_shoulder - 1])
            cylinder(d = pay_id - shoulder_clear - 2*1.0, h = nose_shoulder + nose_wall + 2);
    }
}

// ============================================================== DUMMIES
module motor_dummy(z, col) {
    color(col, 0.6) translate([0, 0, z]) cylinder(d = motor_d, h = motor_len);
}

module electronics_dummy(z_pay) {
    color("green", 0.7)
        translate([-3.5/2, -vtx_w/2, z_pay]) cube([3.5, vtx_w, vtx_w]);
    color("blue", 0.6)
        translate([-pay_id/2 + 2, -batt_w/2, z_pay + 2]) cube([batt_t, batt_w, batt_len]);
}

module camera_dummy() {
    cam_frame() {
        color("black") {
            translate([-cam_h/2, -cam_w/2, -cam_body_len]) cube([cam_h, cam_w, cam_body_len]);
            cylinder(d = lens_d, h = lens_len - 0.3);
        }
        color("silver") translate([0, 0, -cam_screw_back]) rotate([90, 0, 0])
            cylinder(d = 2, h = cam_w + 5, center = true);
    }
}

// ============================================================== OUTPUT
module assembly() {
    color("orange") body();
    motor_dummy(0, "red");            // C6-0 booster
    motor_dummy(motor_len, "yellow"); // C6-5 / C6-7 sustainer
    z_payload = body_len - shoulder_len;
    color("white") translate([0, 0, z_payload]) payload();
    electronics_dummy(z_payload + shoulder_len + trans_len);
    translate([0, 0, z_payload + shoulder_len + trans_len + pay_len]) {
        color("gray") nose();
        camera_dummy();
    }
}

module section() {
    // assembly cut in half along the XZ plane to show the insides
    difference() {
        assembly();
        translate([-100, -200, -10]) cube([200, 200, 600]);
    }
}

if (part == "assembly")  assembly();
if (part == "section")   section();
if (part == "body")      body();
if (part == "payload")   payload();
if (part == "nose")      translate([0, 0, nose_shoulder]) nose();
if (part == "all_print") {
    body();
    translate([55, 0, 0]) payload();
    translate([100, 0, nose_shoulder]) nose();
}
