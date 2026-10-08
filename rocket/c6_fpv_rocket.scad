// =====================================================================
//  Two-stage FPV rocket (C11-0 booster -> C6 sustainer) - fully 3D printed
//  Camera: Walksnail Ascent Lite kit (VTX 30.5x30.5x3.5, cam 12x14x15)
//
//  Layout (single airframe, "motor-eject" staging):
//    - Minimum-diameter body: the body IS the motor tube.
//    - Booster C11-0 (24 mm) sits in a wider aft section. Its top pushes on
//      a printed cone step; the C6 sustainer (18 mm) sits right above it.
//    - When the C11-0 burns through it lights the sustainer and the
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

/* [Motors] */
booster_d      = 24.0;   // Estes C11-0: 24 x 70 mm
booster_len    = 70.0;
motor_d        = 18.0;   // Estes C6-5 / C6-7 sustainer: 18 x 70 mm
motor_len      = 70.0;
motor_clear    = 0.4;    // diametral clearance for the printed bores
aft_taper      = 15;     // smooth step from booster section to upper body

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
lug_z          = 95;     // bottom of lug from aft end

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
nose_wall      = 0.8;
nose_shoulder  = 10;
tip_round      = 2.0;    // small rounded point
cam_w          = 14.0;   // camera body width  (tangential, M2 side holes)
cam_h          = 12.0;   // camera body height (radial)
cam_body_len   = 10.0;   // body depth behind the lens  (MEASURE yours)
lens_d         = 8.0;    // lens barrel diameter          (MEASURE yours)
lens_len       = 5.0;    // lens barrel past body front   (MEASURE yours)
cam_fit        = 0.5;    // total clearance around the camera
cable_room     = 5.0;    // space behind the camera for the coax to bend inward
cam_screws     = true;   // M2 side holes (or just glue the camera in)
cam_screw_back = 5.0;    // M2 side hole: distance behind body front (MEASURE)
cam_screw_d    = 2.3;
cam_tilt       = 12;     // lens tilted outward from straight down (deg)
cam_out        = 0.5;    // lens axis this far outside the payload bay skin
cam_lens_z     = 3.5;    // height of lens centre above nose base
pod_angle      = 60;     // around the body: 60 = between two fins
pod_wall       = 1.0;
pod_round      = 2.5;    // corner radius of the pod
pod_taper      = 45;     // length of the streamlined fairing ahead of the camera

// ---------------------------------------------------------------- derived
bore      = motor_d + motor_clear;        // sustainer bore
bore_b    = booster_d + motor_clear;      // booster bore
body_od   = bore + 2*wall;                // upper body
aft_od    = bore_b + 2*wall;              // booster section
step_h    = (bore_b - bore)/2;            // 45 deg cone step between bores
motor_sec = booster_len + step_h + motor_len;
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
    // fin in XZ plane, root on the body surface; all edges fully rounded
    pts = [[0, 0], [0, fin_root], [fin_span, fin_root - fin_le_sweep],
           [fin_span, fin_root - fin_le_sweep - fin_tip]];
    translate([aft_od/2 - 0.6, 0, 0])
        hull() for (q = pts) translate([q[0], 0, q[1]]) sphere(d = fin_t, $fn = 24);
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
    intersection() {                      // flat bottom for the print bed
    translate([-200, -200, 0]) cube([400, 400, 1000]);
    difference() {
        union() {
            cylinder(d = body_od, h = body_len);
            cylinder(d = aft_od, h = booster_len);
            translate([0, 0, booster_len - eps])
                cylinder(d1 = aft_od, d2 = body_od, h = aft_taper);
            for (i = [0:n_fins-1]) rotate([0, 0, i*360/n_fins]) fin();
            launch_lug();
        }
        // booster bore, 45 deg step (booster thrust bears on it), sustainer bore
        translate([0, 0, -1]) cylinder(d = bore_b, h = booster_len + 1);
        translate([0, 0, booster_len - eps]) cylinder(d1 = bore_b, d2 = bore, h = step_h + 2*eps);
        translate([0, 0, booster_len]) cylinder(d = bore, h = motor_sec - booster_len);
        // gas passage through thrust ring
        cylinder(d = thrust_ring_id, h = body_len);
        // recovery bay
        translate([0, 0, motor_sec + thrust_ring_h])
            cylinder(d = bore, h = bay_len + 1);
        // shock cord tie holes (cross hole through both walls)
        translate([0, 0, body_len - 30])
            rotate([90, 0, 0]) cylinder(d = 2.2, h = body_od + 2, center = true);
        // small chamfer on bore entry
        translate([0, 0, -eps]) cylinder(d1 = bore_b + 1, d2 = bore_b, h = 0.8);
    }
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

function flare_r(t) = body_od/2 + (pay_od - body_od)/2 * (1 - cos(180*t))/2;

module flare(off, z0) {
    n = 30;
    pts = [ for (i = [0:n]) [flare_r(i/n) - off, z0 + trans_len*i/n] ];
    rotate_extrude() polygon(concat([[0, z0]], pts, [[0, z0 + trans_len + eps]]));
}

module payload() {
    z_tr  = shoulder_len;               // transition start
    z_pay = shoulder_len + trans_len;   // straight section start
    difference() {
        union() {
            // shoulder into body
            cylinder(d = bore - shoulder_clear, h = shoulder_len + eps);
            // flare (cosine S-curve, tangent at both ends)
            flare(0, z_tr);
            // straight bay
            translate([0, 0, z_pay]) cylinder(d = pay_od, h = pay_len);
        }
        // hollow shoulder (cord anchor bar is added back later)
        translate([0, 0, -1])
            cylinder(d = bore - shoulder_clear - 2*1.0, h = shoulder_len + 1 - eps);
        // hollow flare above bulkhead
        intersection() {
            flare(pay_wall, z_tr);
            translate([0, 0, z_tr + bulkhead_t]) cylinder(r = 50, h = trans_len);
        }
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

// --------------------------------------------------------- camera pod
// Camera frame: origin = centre of camera body front face, local +Z = view
// direction (down, tilted out), local +X = radially inward, local Y = tangential.
lens_x = nose_R + cam_out;
cam_o  = [lens_x - lens_len*sin(cam_tilt), 0, cam_lens_z + lens_len*cos(cam_tilt)];
// local -> global (before pod_angle rotation)
function c2g(p) = cam_o + [-p[0]*cos(cam_tilt) + p[2]*sin(cam_tilt), p[1],
                           -p[0]*sin(cam_tilt) - p[2]*cos(cam_tilt)];

module cam_frame() {
    rotate([0, 0, pod_angle]) translate(cam_o) rotate([0, 180 - cam_tilt, 0]) children();
}

// pod block: rounded box hugging the camera, flat aft face flush with the lens
pod_hx = cam_h/2 + cam_fit/2 + pod_wall;      // half size radial
pod_hy = cam_w/2 + cam_fit/2 + pod_wall;      // half size tangential
pod_zb = -(cam_body_len + cable_room + pod_wall);   // back of block (local z)
pod_zf = lens_len - 0.3;                             // aft face (lens pokes 0.3 out)

module pod_block() {
    r = pod_round;
    hull() {
        // back corners: spheres
        for (x = [-1, 1], y = [-1, 1])
            translate([x*(pod_hx - r), y*(pod_hy - r), pod_zb + r]) sphere(r, $fn = 32);
        // aft face corners: flat-bottomed so the face stays a clean plane
        for (x = [-1, 1], y = [-1, 1])
            translate([x*(pod_hx - r), y*(pod_hy - r), pod_zf - r])
                cylinder(r = r, h = r, $fn = 32);
    }
}

// streamlined fairing ahead of the block: a loft of rounded sections that
// shrink with a parabolic profile and slide in onto the ogive skin
function sec_s(t) = 1 - t*t;
module pod_section(t) {
    top_out = c2g([-pod_hx, 0, pod_zb]);   // outer top edge of the block
    z  = top_out[2] + pod_taper*t;
    s  = max(sec_s(t), 0.04);
    hx = pod_hx*s; hy = pod_hy*s; r = min(pod_round, hx, hy);
    e  = top_out[0] + (nose_r(z) - 0.2 - top_out[0])*pow(t, 1.3);   // outer edge
    translate([e - hx, 0, z])
        hull() for (x = [-1, 1], y = [-1, 1])
            translate([x*(hx - r), y*(hy - r), 0]) sphere(r, $fn = 24);
}

module pod_envelope() {
    n = 14;
    rotate([0, 0, pod_angle]) {
        hull() { rotate([0, 0, -pod_angle]) cam_frame() pod_block(); pod_section(0); }
        for (i = [0:n-1]) hull() { pod_section(i/n); pod_section((i+1)/n); }
    }
}

module cam_pocket() {
    cam_frame() {
        // camera body + cable room, open towards the nose interior (+X)
        translate([-(cam_h + cam_fit)/2, -(cam_w + cam_fit)/2, -(cam_body_len + cable_room)])
            cube([cam_h + cam_fit + 15, cam_w + cam_fit, cam_body_len + cable_room + eps]);
        // lens window
        translate([0, 0, -1]) cylinder(d = lens_d + cam_fit, h = lens_len + 5);
        if (cam_screws)
            translate([0, 0, -cam_screw_back]) rotate([90, 0, 0])
                cylinder(d = cam_screw_d, h = 2*pod_hy + 4, center = true, $fn = 24);
    }
}

module nose() {
    difference() {
        union() {
            difference() {
                nose_outer();
                translate([0, 0, -eps]) nose_outer(nose_wall);
            }
            // pod: fairing only outside the nose, full block around the camera
            intersection() {
                union() {
                    difference() { pod_envelope(); nose_outer(nose_wall); }
                    cam_frame() pod_block();
                }
                translate([-100, -100, 0]) cube([200, 200, 200]);   // nothing below base
            }
            // base ring tying shell to shoulder
            cylinder(r = nose_R - 0.2, h = nose_wall);
            // shoulder into payload bay
            translate([0, 0, -nose_shoulder])
                cylinder(d = pay_id - shoulder_clear, h = nose_shoulder + eps);
        }
        cam_pocket();
        // hollow shoulder
        translate([0, 0, -nose_shoulder - 1])
            cylinder(d = pay_id - shoulder_clear - 2*1.0, h = nose_shoulder + nose_wall + 2);
    }
}

// ============================================================== DUMMIES
module motor_dummy(z, col, d = motor_d, l = motor_len) {
    color(col, 0.6) translate([0, 0, z]) cylinder(d = d, h = l);
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
        // coax leaving the back of the camera, bending into the nose
        color("dimgray") translate([0, 0, -cam_body_len - 2]) rotate([0, 90, 0]) cylinder(d = 1.5, h = 14, $fn = 12);
    }
}

// ============================================================== OUTPUT
module assembly() {
    color("orange") body();
    motor_dummy(0, "red", booster_d, booster_len);      // C11-0 booster
    motor_dummy(booster_len + step_h, "yellow");        // C6-5 / C6-7 sustainer
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
