const RAW = {
  Chest: "Bench press:pu,Incline bench press:pu,Decline bench press:pu,Dumbbell fly:ra,Incline dumbbell fly:ra,Cable crossover:ra,Push-up:pu,Wide push-up:pu,Diamond push-up:pu,Decline push-up:pu,Dips:pu,Pec deck:ra,Machine chest press:pu,Svend press:m,Dumbbell pullover:m",
  Back: "Lat pulldown:pl,Pull-up:pl,Chin-up:pl,Barbell row:pl,Dumbbell row:pl,Seated cable row:pl,T-bar row:pl,Single-arm cable row:pl,Straight-arm pulldown:ra,Face pull:pl,Deadlift:hg,Rack pull:hg,Inverted row:pl,Back extension:hg,Meadows row:pl",
  Legs: "Back squat:sq,Front squat:sq,Goblet squat:sq,Leg press:sq,Lunge:sq,Walking lunge:sq,Bulgarian split squat:sq,Romanian deadlift:hg,Leg extension:sq,Leg curl:sq,Hip thrust:hg,Glute bridge:hg,Step-up:sq,Calf raise:m,Hack squat:sq",
  Shoulders: "Overhead press:pu,Dumbbell shoulder press:pu,Arnold press:pu,Lateral raise:ra,Front raise:ra,Rear delt fly:ra,Upright row:pl,Cable lateral raise:ra,Face pull:pl,Machine shoulder press:pu,Pike push-up:pu,Landmine press:pu,Shrug:m,Reverse pec deck:ra,Handstand push-up:pu",
  Arms: "Barbell curl:cu,Dumbbell curl:cu,Hammer curl:cu,Preacher curl:cu,Concentration curl:cu,Cable curl:cu,Incline curl:cu,Triceps pushdown:pu,Overhead triceps extension:pu,Skull crusher:pu,Close-grip bench press:pu,Triceps kickback:pu,Bench dip:pu,Reverse curl:cu,Wrist curl:m",
  Core: "Plank:t,Side plank:t,Hollow hold:t,Crunch:cr,Bicycle crunch:m,Hanging knee raise:cr,Leg raise:cr,Russian twist:m,Mountain climber:m,Dead bug:m,Bird dog:m,Ab wheel rollout:m,Cable crunch:cr,Sit-up:cr,Flutter kick:m"
};
const GROUPS = {};
for (const g in RAW) GROUPS[g] = RAW[g].split(",").map(s => { const i = s.lastIndexOf(":"); return { name: s.slice(0, i), fam: s.slice(i + 1), group: g }; });
const ALL = Object.values(GROUPS).flat();
const COLORS = { Chest: "#ff7a1a", Back: "#2f80ff", Legs: "#22d37a", Shoulders: "#ffb020", Arms: "#ff4fa3", Core: "#3ddc97" };
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

// Joint angle used for counting. Points are MediaPipe landmark names without the side prefix.
const JOINTS = {
  knee:  ["hip", "knee", "ankle"],
  hip:   ["shoulder", "hip", "knee"],
  elbow: ["shoulder", "elbow", "wrist"],
  abd:   ["hip", "shoulder", "elbow"]
};

// One line per exercise: name|joint|low|high|depth|view|invert|lean
// low/high: hysteresis band (degrees). depth: a rep must reach this angle or lower.
// view: where to film from. invert: 1 flips the angle (for raises and flies). lean: check torso lean (squats).
// Starting values. Test each lift and adjust.
const CAM_TABLE = `
Bench press|elbow|90|160|90|side|0|0
Incline bench press|elbow|90|160|90|side|0|0
Decline bench press|elbow|90|160|90|side|0|0
Dumbbell fly|abd|110|150|100|front|1|0
Incline dumbbell fly|abd|110|150|100|front|1|0
Cable crossover|abd|110|150|100|front|1|0
Push-up|elbow|120|160|90|side|0|0
Wide push-up|elbow|120|160|90|side|0|0
Diamond push-up|elbow|120|160|90|side|0|0
Decline push-up|elbow|120|160|90|side|0|0
Dips|elbow|90|160|90|side|0|0
Pec deck|abd|110|150|100|front|1|0
Machine chest press|elbow|90|160|90|side|0|0
Lat pulldown|elbow|90|155|90|side|0|0
Pull-up|elbow|90|160|90|side|0|0
Chin-up|elbow|90|160|90|side|0|0
Barbell row|elbow|90|155|90|side|0|0
Dumbbell row|elbow|90|155|90|side|0|0
Seated cable row|elbow|90|155|90|side|0|0
T-bar row|elbow|90|155|90|side|0|0
Single-arm cable row|elbow|90|155|90|side|0|0
Straight-arm pulldown|abd|70|150|40|side|0|0
Face pull|elbow|80|150|90|side|0|0
Deadlift|hip|120|165|110|side|0|0
Rack pull|hip|120|165|110|side|0|0
Inverted row|elbow|90|155|90|side|0|0
Back extension|hip|110|160|110|side|0|0
Meadows row|elbow|90|155|90|side|0|0
Back squat|knee|145|165|100|side|0|1
Front squat|knee|130|160|100|side|0|1
Goblet squat|knee|130|160|100|side|0|1
Hack squat|knee|130|160|100|side|0|1
Leg press|knee|100|160|90|side|0|0
Lunge|knee|120|160|100|side|0|0
Walking lunge|knee|120|160|100|side|0|0
Bulgarian split squat|knee|120|160|100|side|0|0
Step-up|knee|120|160|100|side|0|0
Romanian deadlift|hip|120|165|110|side|0|0
Leg extension|knee|100|160|100|side|0|0
Leg curl|knee|100|160|90|side|0|0
Hip thrust|hip|110|160|110|side|0|0
Glute bridge|hip|110|160|110|side|0|0
Overhead press|elbow|90|160|90|side|0|0
Dumbbell shoulder press|elbow|90|160|90|side|0|0
Arnold press|elbow|90|160|90|side|0|0
Machine shoulder press|elbow|90|160|90|side|0|0
Landmine press|elbow|90|160|90|side|0|0
Handstand push-up|elbow|90|160|90|side|0|0
Pike push-up|elbow|120|160|90|side|0|0
Lateral raise|abd|110|155|100|front|1|0
Cable lateral raise|abd|110|155|100|front|1|0
Reverse pec deck|abd|110|155|100|front|1|0
Rear delt fly|abd|110|150|100|front|1|0
Front raise|abd|110|155|100|side|1|0
Upright row|elbow|70|150|80|side|0|0
Barbell curl|elbow|70|150|60|side|0|0
Dumbbell curl|elbow|70|150|60|side|0|0
Hammer curl|elbow|70|150|60|side|0|0
Preacher curl|elbow|70|150|60|side|0|0
Concentration curl|elbow|70|150|60|side|0|0
Cable curl|elbow|70|150|60|side|0|0
Incline curl|elbow|70|150|60|side|0|0
Reverse curl|elbow|70|150|60|side|0|0
Triceps pushdown|elbow|90|160|90|side|0|0
Overhead triceps extension|elbow|60|160|60|side|0|0
Skull crusher|elbow|90|160|90|side|0|0
Close-grip bench press|elbow|90|160|90|side|0|0
Triceps kickback|elbow|90|160|90|side|0|0
Bench dip|elbow|90|160|90|side|0|0
Crunch|hip|110|155|110|side|0|0
Hanging knee raise|hip|110|160|110|side|0|0
Leg raise|hip|110|160|110|side|0|0
Cable crunch|hip|110|155|110|side|0|0
Sit-up|hip|110|160|110|side|0|0
`;

const CAM = {};
CAM_TABLE.trim().split("\n").forEach(line => {
  const [name, joint, low, high, depth, view, inv, lean] = line.split("|");
  CAM[name] = { j: JOINTS[joint], low: +low, high: +high, depth: +depth, view, inv: inv === "1", lean: lean === "1" };
});

const modeOf = f => f === "t" ? "Timer" : f === "m" ? "Tap count" : "Auto count";
function modeFor(ex) {
  if (CAM[ex.name]) return "Auto count";
  return ex.fam === "t" ? "Timer" : "Tap count";
}

// Short form cues by movement type
const CUES = {
  sq: "Brace your core, sit the hips back and down, keep the knees tracking over the toes, and drive up through the whole foot.",
  hg: "Hinge at the hips with a flat back, keep the load close to the body, and drive the hips forward to stand tall.",
  cr: "Keep the lower back supported, move through the torso or legs with control, and breathe out on the way up.",
  pu: "Keep the wrists under the elbows, move with control, and press to full extension without shrugging.",
  pl: "Start from a full stretch, pull the elbows down and back, squeeze the shoulder blades, then lower with control.",
  cu: "Keep the upper arms still, curl through a full range, and lower slowly without swinging.",
  ra: "Keep a soft bend in the elbows, raise to shoulder height with control, and avoid swinging.",
  m: "Move slowly through the full range and keep the core braced. Tap once for each rep.",
  t: "Hold the position with a neutral spine and steady breathing. Stop when your form breaks."
};

function tileHTML(e) {
  return `<a class="tile" href="/workout?g=${encodeURIComponent(e.group)}&e=${encodeURIComponent(e.name)}" style="--c:${COLORS[e.group]}">
    <img src="/static/images/${slug(e.name)}.jpg" alt="" onerror="this.remove()">
    <span class="tag">${esc(e.group)}</span>
    <h3 class="disp">${esc(e.name)}</h3>
    <span style="color:var(--green);font-weight:700">Open workout →</span></a>`;
}
