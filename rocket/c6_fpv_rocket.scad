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
//      bay, battery beside it, camera looks forward out of the nose tip.
//
//  Select what to render/export with `part`.
// =====================================================================

part = "assembly"; // [assembly, body, payload, nose, all_print]

/* [Quality] */
$fn = 96;

/* [Motors - Estes C6 (18 x 70 mm)] */
motor_d        = 18.0;
motor_len      = 70.0;
motor_clear    = 0.4;    // diametral clearance for the printed bore
n_motors       = 2;      // booster + sustainer stacked in the tube

/* [Body] */
wall           = 1.2;    // body wall
thrust_ring_h  = 3.0;
thrust_ring_id = 13.0;   // ejection gas passes through this
bay_len        = 85;     // recovery bay above the thrust ring

/* [Fins] */
n_fins         = 3;
fin_root       = 65;
fin_tip        = 25;
fin_span       = 42;
fin_le_sweep   = 32;     // leading edge sweep (along body axis)
fin_t          = 2.4;

/* [Launch lug - 1/8 in rod] */
lug_id         = 3.8;
lug_wall       = 1.0;
lug_len        = 40;
lug_z          = 75;     // bottom of lug from aft end

/* [Payload bay] */
pay_wall       = 1.6;
pay_id         = 32.0;   // VTX 30.5 board stands vertically -> needs ~31.5
pay_len        = 52;     // straight section length
trans_len      = 25;     // body -> payload flare
shoulder_len   = 20;     // slides into top of body
shoulder_clear = 0.3;
bulkhead_t     = 2.5;

/* [Walksnail Ascent Lite VTX] */
vtx_w          = 30.5;
vtx_t          = 5.0;    // board 3.5 + parts; slot width
vtx_guide_d    = 3.0;    // how far the guides reach in from the wall

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
nose_len       = 70;
nose_wall      = 1.6;
nose_shoulder  = 12;
tip_r          = 11;     // flat front face radius (camera window)
cam_w          = 14.0;   // camera body
cam_h          = 12.0;
cam_d          = 15.0;
cam_fit        = 0.4;
lens_d         = 10.0;   // hole in front face

// ---------------------------------------------------------------- derived
bore      = motor_d + motor_clear;
body_od   = bore + 2*wall;
motor_sec = n_motors*motor_len;
body_len  = motor_sec + thrust_ring_h + bay_len;
pay_od    = pay_id + 2*pay_wall;
nose_R    = pay_od/2;
rho       = (nose_R*nose_R + nose_len*nose_len) / (2*nose_R);
// height above nose base where the ogive radius drops to tip_r
nose_cut  = sqrt(rho*rho - pow(tip_r - nose_R + rho, 2));
eps = 0.01;

echo(str("Body OD = ", body_od, " mm, body length = ", body_len, " mm"));
echo(str("Payload OD = ", pay_od, " mm"));
echo(str("Overall length ~ ", body_len + trans_len + pay_len + nose_cut, " mm"));

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
            cylinder(d = bore - shoulder_clear - 2*1.4, h = shoulder_len + 1 - eps);
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

module ogive_solid(R, off = 0) {
    // rotate_extrude profile of tangent ogive, z = 0 at base, truncated at nose_cut
    steps = 60;
    pts = [ for (i = [0:steps])
              let(z = nose_cut*i/steps,
                  x = nose_len - z,                    // distance from virtual tip
                  r = sqrt(rho*rho - pow(nose_len - x, 2)) + nose_R - rho)
              [max(r - off, 0.01), z] ];
    rotate_extrude() polygon(concat([[0, 0]], pts, [[0, nose_cut]]));
}

module nose() {
    cam_box = [cam_w + cam_fit, cam_h + cam_fit, cam_d];
    face_t  = nose_wall;
    difference() {
        union() {
            // shell
            difference() {
                ogive_solid(nose_R);
                translate([0, 0, -eps]) ogive_solid(nose_R, nose_wall);
            }
            // solid front face
            translate([0, 0, nose_cut - face_t])
                cylinder(r = tip_r, h = face_t);
            // camera sleeve
            intersection() {
                ogive_solid(nose_R);
                translate([0, 0, nose_cut - cam_d/2])
                    cube([cam_box.x + 2.4, cam_box.y + 2.4, cam_d], center = true);
            }
            // base ring tying shell to shoulder
            cylinder(r = nose_R - 0.2, h = nose_wall);
            // shoulder into payload bay
            translate([0, 0, -nose_shoulder])
                cylinder(d = pay_id - shoulder_clear, h = nose_shoulder + eps);
        }
        // camera pocket (open at the back for loading + cable)
        translate([0, 0, nose_cut - face_t - cam_d/2 - 0.5])
            cube([cam_box.x, cam_box.y, cam_d + 1], center = true);
        // lens window
        translate([0, 0, nose_cut - face_t - 1]) cylinder(d = lens_d, h = face_t + 2);
        // hollow shoulder
        translate([0, 0, -nose_shoulder - 1])
            cylinder(d = pay_id - shoulder_clear - 2*1.4, h = nose_shoulder + nose_wall + 2);
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

// ============================================================== OUTPUT
module assembly() {
    color("orange") body();
    motor_dummy(0, "red");            // C6-0 booster
    motor_dummy(motor_len, "yellow"); // C6-5 / C6-7 sustainer
    z_payload = body_len - shoulder_len;
    color("white") translate([0, 0, z_payload]) payload();
    electronics_dummy(z_payload + shoulder_len + trans_len);
    color("gray")
        translate([0, 0, z_payload + shoulder_len + trans_len + pay_len]) nose();
}

if (part == "assembly")  assembly();
if (part == "body")      body();
if (part == "payload")   payload();
if (part == "nose")      translate([0, 0, nose_shoulder]) nose();
if (part == "all_print") {
    body();
    translate([60, 0, 0]) payload();
    translate([110, 0, nose_shoulder]) nose();
}
