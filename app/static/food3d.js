import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

// Floating healthy foods as 3D shapes. Sits behind the page content.
const canvas = document.createElement("canvas");
canvas.id = "bg3d";
document.body.prepend(canvas);

const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000000, 0);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
camera.position.set(0, 0, 16);

scene.add(new THREE.AmbientLight(0xffffff, 0.75));
const sun = new THREE.DirectionalLight(0xffffff, 1.0);
sun.position.set(5, 8, 6);
scene.add(sun);
const leafLight = new THREE.PointLight(0x22d37a, 2, 20);
leafLight.position.set(-6, 2, 4);
scene.add(leafLight);

const mat = (color, roughness = 0.45) =>
  new THREE.MeshStandardMaterial({ color, roughness, metalness: 0.05 });

// Each builder returns one food. Shapes stand in for the real foods.
const builders = [
  () => new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 32), mat(0xe74c3c)),          // apple
  () => new THREE.Mesh(new THREE.SphereGeometry(0.75, 32, 32), mat(0xff9f1a)),         // orange
  () => {                                                                               // carrot
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.ConeGeometry(0.45, 1.8, 24), mat(0xf57c20));
    body.rotation.x = Math.PI;
    const top = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.6, 12), mat(0x2ecc71));
    top.position.y = 1.2;
    g.add(body, top);
    return g;
  },
  () => new THREE.Mesh(new THREE.IcosahedronGeometry(0.85, 1), mat(0x27ae60)),         // broccoli
  () => new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.22, 16, 40, Math.PI * 0.6), mat(0xf7d33e)), // banana
  () => new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 16), mat(0x3b4cca, 0.3)),    // blueberry
  () => new THREE.Mesh(new THREE.DodecahedronGeometry(0.7, 0), mat(0xc0392b)),          // pepper
  () => {                                                                               // leaf
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.6, 24, 24), mat(0x2ecc71, 0.6));
    leaf.scale.set(0.6, 1.1, 0.12);
    return leaf;
  }
];

const items = [];
for (let i = 0; i < 20; i++) {
  const obj = builders[i % builders.length]();
  obj.position.set((Math.random() - 0.5) * 26, (Math.random() - 0.5) * 16, -4 - Math.random() * 6);
  obj.scale.multiplyScalar(0.6 + Math.random() * 0.8);
  obj.userData = {
    rx: (Math.random() - 0.5) * 0.012,
    ry: (Math.random() - 0.5) * 0.015,
    phase: Math.random() * Math.PI * 2,
    speed: 0.3 + Math.random() * 0.5,
    baseY: obj.position.y
  };
  scene.add(obj);
  items.push(obj);
}

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

const clock = new THREE.Clock();
function tick() {
  const t = clock.getElapsedTime();
  for (const o of items) {
    o.rotation.x += o.userData.rx;
    o.rotation.y += o.userData.ry;
    o.position.y = o.userData.baseY + Math.sin(t * o.userData.speed + o.userData.phase) * 0.6;
  }
  camera.position.x += (mx * 2 - camera.position.x) * 0.03;
  camera.position.y += (-my * 2 - camera.position.y) * 0.03;
  camera.lookAt(0, 0, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
tick();
