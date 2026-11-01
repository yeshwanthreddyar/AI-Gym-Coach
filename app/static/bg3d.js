import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

const canvas = document.createElement("canvas");
canvas.id = "bg3d";
document.body.prepend(canvas);

const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000000, 0);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
camera.position.set(0, 0.5, 14);

// Lights: soft fill, green rim light, warm orange key
scene.add(new THREE.AmbientLight(0xffffff, 0.5));
const key = new THREE.DirectionalLight(0xffffff, 1.1);
key.position.set(4, 6, 6);
scene.add(key);
const rim = new THREE.DirectionalLight(0x22d37a, 1.8);
rim.position.set(-6, 3, -4);
scene.add(rim);
const warm = new THREE.PointLight(0xff7a1a, 2.5, 14);
warm.position.set(3, 1, 4);
scene.add(warm);

// ---------- 3D gym figure (built from shapes) ----------
const skin = new THREE.MeshStandardMaterial({ color: 0x3a4152, roughness: 0.45, metalness: 0.25 });
const shorts = new THREE.MeshStandardMaterial({ color: 0xff7a1a, roughness: 0.4, metalness: 0.1 });
const accent = new THREE.MeshStandardMaterial({ color: 0x22d37a, roughness: 0.3, metalness: 0.4, emissive: 0x0b3a22 });

// A limb hangs down from its pivot point
function limb(len, r, mat) {
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 6, 14), mat);
  m.position.y = -(len / 2 + r);
  return m;
}

const figure = new THREE.Group();
const hips = new THREE.Group();
figure.add(hips);

const pelvis = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.5, 0.5), shorts);
hips.add(pelvis);

const torso = new THREE.Group();
torso.position.y = 0.25;
hips.add(torso);

const chest = new THREE.Mesh(new THREE.CapsuleGeometry(0.45, 0.9, 8, 16), skin);
chest.position.y = 0.6;
chest.scale.set(1.25, 1, 0.8);
torso.add(chest);

const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.2, 0.9), accent);
stripe.position.set(0, 0.6, 0);
torso.add(stripe);

const head = new THREE.Mesh(new THREE.SphereGeometry(0.34, 24, 24), skin);
head.position.y = 1.85;
torso.add(head);

const arms = [];
for (const s of [-1, 1]) {
  const shoulder = new THREE.Group();
  shoulder.position.set(0.62 * s, 1.25, 0);
  torso.add(shoulder);
  shoulder.add(limb(0.6, 0.14, skin));
  const elbow = new THREE.Group();
  elbow.position.y = -0.88;
  shoulder.add(elbow);
  elbow.add(limb(0.55, 0.12, skin));
  const hand = new THREE.Mesh(new THREE.SphereGeometry(0.14, 12, 12), skin);
  hand.position.y = -0.7;
  elbow.add(hand);
  arms.push({ shoulder, elbow });
}

const legs = [];
for (const s of [-1, 1]) {
  const hip = new THREE.Group();
  hip.position.set(0.25 * s, -0.25, 0);
  hips.add(hip);
  hip.add(limb(0.9, 0.2, skin));
  const knee = new THREE.Group();
  knee.position.y = -1.3;
  hip.add(knee);
  knee.add(limb(0.85, 0.17, skin));
  const foot = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.14, 0.45), accent);
  foot.position.set(0, -1.12, 0.12);
  knee.add(foot);
  legs.push({ hip, knee });
}

const HIP_BASE = 2.32; // height of the hips above the floor when standing
figure.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.01, 0.01), skin)); // keeps the group valid
figure.position.set(5.4, -4.4, -1);
figure.scale.setScalar(1.25);
scene.add(figure);

// ---------- background shapes and particles ----------
const COLORS = [0xff7a1a, 0x22d37a, 0x2f80ff];
const GEOS = [
  () => new THREE.IcosahedronGeometry(1, 0),
  () => new THREE.TorusGeometry(0.8, 0.25, 12, 40),
  () => new THREE.OctahedronGeometry(1, 0)
];
const shapes = [];
for (let i = 0; i < 12; i++) {
  const mesh = new THREE.Mesh(GEOS[i % 3](), new THREE.MeshBasicMaterial({
    color: COLORS[i % 3], wireframe: true, transparent: true, opacity: 0.25
  }));
  mesh.position.set(-11 + Math.random() * 14, (Math.random() - 0.5) * 16, -6 - Math.random() * 6);
  mesh.scale.setScalar(0.6 + Math.random() * 1.2);
  mesh.userData = {
    rx: (Math.random() - 0.5) * 0.01,
    ry: (Math.random() - 0.5) * 0.012,
    phase: Math.random() * Math.PI * 2,
    speed: 0.3 + Math.random() * 0.5,
    baseY: mesh.position.y
  };
  scene.add(mesh);
  shapes.push(mesh);
}

const N = 500;
const pos = new Float32Array(N * 3);
for (let i = 0; i < N * 3; i++) pos[i] = (Math.random() - 0.5) * 40;
const pGeo = new THREE.BufferGeometry();
pGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
const points = new THREE.Points(pGeo, new THREE.PointsMaterial({
  color: 0x22d37a, size: 0.06, transparent: true, opacity: 0.55
}));
scene.add(points);

// ---------- interaction and resize ----------
let mx = 0, my = 0;
window.addEventListener("pointermove", e => {
  mx = e.clientX / window.innerWidth - 0.5;
  my = e.clientY / window.innerHeight - 0.5;
});
function resize() {
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();

// ---------- animation ----------
const clock = new THREE.Clock();
function tick() {
  const t = clock.getElapsedTime();

  // Squat cycle, about 3.2 s per rep: d goes 0 (standing) -> 1 (bottom) -> 0
  const d = (1 - Math.cos((2 * Math.PI * t) / 3.2)) / 2;

  hips.position.y = HIP_BASE - d * 0.9 - 0.5 * 0; // hips drop as you squat
  torso.rotation.x = -d * 0.35;                    // chest leans forward
  for (const L of legs) {
    L.hip.rotation.x = -d * 1.2;                   // thigh forward
    L.knee.rotation.x = d * 0.9;                   // knee bends
  }
  for (const A of arms) {
    A.shoulder.rotation.x = -0.2 - d * 0.6;        // arms reach forward as you squat
    A.elbow.rotation.x = -0.15;
  }
  figure.rotation.y = -0.35 + Math.sin(t * 0.4) * 0.12; // gentle sway

  for (const m of shapes) {
    m.rotation.x += m.userData.rx;
    m.rotation.y += m.userData.ry;
    m.position.y = m.userData.baseY + Math.sin(t * m.userData.speed + m.userData.phase) * 0.6;
  }
  points.rotation.y = t * 0.02;

  camera.position.x += (mx * 2 - camera.position.x) * 0.03;
  camera.position.y += (0.5 - my * 2 - camera.position.y) * 0.03;
  camera.lookAt(0, -0.5, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
tick();
