import * as T from 'three';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { NeuralFrame } from './circuit';
import type { PhysicsFrame } from './physics';
import { aimJoint, plantLeg, applyPhysicalPose } from './fly-pose';
import { flySurfaceMaps, softenSurface, surfaceUV } from './fly-surfaces';
import { CAMERA_PRESETS } from './camera-presets';
import { createJointRig, type Rig } from './fly-rig';

export interface LiveDrawing { frame: NeuralFrame | null; drawing: boolean; run: number; physical: PhysicsFrame | null; ink: PhysicsFrame[]; wings: boolean; wing: number; resetView: number; cameraPreset: number; }
const UP = new T.Vector3(0, 1, 0);

function box(w: number, h: number, d: number, color: string, x: number, y: number, z: number, scene: T.Object3D) {
  const mesh = new T.Mesh(new T.BoxGeometry(w, h, d), new T.MeshStandardMaterial({ color, roughness: .73 }));
  mesh.position.set(x, y, z); mesh.castShadow = true; mesh.receiveShadow = true; scene.add(mesh); return mesh;
}

/** Anatomical rendering of measured MuJoCo poses. Only actual paper contacts leave ink. */
export function createFlyScene(host: HTMLElement, live: LiveDrawing, ready: () => void, fail: (e: string) => void) {
  const scene = new T.Scene(); scene.background = new T.Color('#151a19');
  const renderer = new T.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.VSMShadowMap; renderer.toneMapping = T.ACESFilmicToneMapping; renderer.toneMappingExposure = .95;
  host.appendChild(renderer.domElement);
  const camera = new T.OrthographicCamera(-4, 4, 2.5, -2.5, .1, 100);
  camera.position.set(3.9, 6.4, 7.6); camera.lookAt(.1, .65, 0);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(.1, .65, 0); controls.enableDamping = true; controls.dampingFactor = .09;
  controls.minPolarAngle = .0001; controls.maxPolarAngle = Math.PI * .49; controls.minZoom = .15; controls.maxZoom = 12; controls.zoomSpeed = 3;
  const applyCameraPreset = () => {
    const preset=CAMERA_PRESETS[live.cameraPreset] || CAMERA_PRESETS[0];
    // Clear pending orbit damping before applying the exact saved preset.
    controls.enableDamping=false;controls.reset();
    camera.position.fromArray(preset.position);controls.target.fromArray(preset.target);
    camera.zoom=preset.zoom;camera.lookAt(controls.target);camera.updateProjectionMatrix();
    controls.update();controls.saveState();controls.enableDamping=true;
    renderer.domElement.dataset.cameraPreset=preset.name;
  };
  applyCameraPreset();
  const resize = () => { const w = host.clientWidth, h = host.clientHeight; renderer.setSize(w, h); const half = Math.max(2.25, 3.05 * h / w); camera.left = -half * w / h; camera.right = half * w / h; camera.top = half; camera.bottom = -half; camera.updateProjectionMatrix(); };
  const observer = new ResizeObserver(resize); observer.observe(host); resize();
  const pmrem = new T.PMREMGenerator(renderer); const room = new RoomEnvironment(); const environment = pmrem.fromScene(room, .04); scene.environment = environment.texture; scene.environmentIntensity = .5; room.dispose(); pmrem.dispose();
  scene.add(new T.HemisphereLight('#fff8e9', '#b7bba8', .65));
  const sun = new T.DirectionalLight('#fff5de', 2.1); sun.position.set(-3, 7, 4); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.camera.left = -5; sun.shadow.camera.right = 5; sun.shadow.camera.top = 5; sun.shadow.camera.bottom = -5; sun.shadow.normalBias = .015; sun.shadow.bias = -.0001; sun.shadow.radius = 4; sun.shadow.blurSamples = 8; scene.add(sun);
  const ground = new T.Mesh(new T.PlaneGeometry(200, 200), new T.MeshBasicMaterial({ color: '#151a19', toneMapped: false })); ground.rotation.x = -Math.PI / 2; ground.position.y = -.04; scene.add(ground);
  const groundShadow = new T.Mesh(new T.PlaneGeometry(200, 200), new T.ShadowMaterial({ color: '#000000', opacity: .48, toneMapped: false }));
  groundShadow.rotation.x = -Math.PI / 2; groundShadow.position.y = -.039; groundShadow.receiveShadow = true; scene.add(groundShadow);
  const grid = new T.GridHelper(200, 800, '#303936', '#252d2b'); grid.position.y = -.0395; scene.add(grid);
  // A small artist's pedestal: weighted base, stem, timber drawing board, loose paper.
  const stand = new T.Mesh(new T.CylinderGeometry(.43, .5, .1, 64), new T.MeshStandardMaterial({ color: '#bfbfba', metalness: .3, roughness: .5 })); stand.position.set(1.55, .035, 0); stand.castShadow = true; stand.receiveShadow = true; scene.add(stand);
  box(.12, .78, .12, '#acaca6', 1.55, .46, 0, scene);
  box(1.24, .075, 1.24, '#b9a07c', 1.55, .885, 0, scene);
  box(1.18, .015, 1.18, '#fffdf5', 1.55, .934, 0, scene);
  const paperCanvas = document.createElement('canvas'); paperCanvas.width = paperCanvas.height = 1024;
  const context = paperCanvas.getContext('2d')!;
  const clearPaper = () => { context.fillStyle = '#fffdf7'; context.fillRect(0, 0, 1024, 1024); };
  clearPaper(); const paperTexture = new T.CanvasTexture(paperCanvas); paperTexture.colorSpace = T.SRGBColorSpace; paperTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const paper = new T.Mesh(new T.PlaneGeometry(1.15, 1.15), new T.MeshStandardMaterial({ map: paperTexture, roughness: 1 })); paper.rotation.x = -Math.PI / 2; paper.position.set(1.55, .946, 0); paper.receiveShadow = true; scene.add(paper);
  // Bent steel wire clips straddle the paper edge; the open loops leave paper visible.
  for (const z of [-.48, .48]) {
    const points = [
      [.035, -.025], [-.047, -.025], [-.067, -.014], [-.067, .014],
      [-.047, .028], [.055, .028], [.072, .014], [.072, -.013],
      [.055, -.036], [-.025, -.036], [-.043, -.022], [-.043, -.005],
      [-.026, .008], [.035, .008],
    ].map(([x, dz]) => new T.Vector3(2.085 + x, .954, z + dz));
    const wire = new T.Mesh(
      new T.TubeGeometry(new T.CatmullRomCurve3(points), 96, .0035, 8, false),
      new T.MeshStandardMaterial({ color: '#b6b9b4', metalness: .88, roughness: .25 }),
    );
    wire.castShadow = true; wire.receiveShadow = true; scene.add(wire);
  }
  const stylus = new T.Group(); scene.add(stylus);
  const shaft = new T.Mesh(new T.CylinderGeometry(.023, .023, .44, 12), new T.MeshStandardMaterial({ color: '#e56835', roughness: .48 })); shaft.position.y = .34; stylus.add(shaft);
  const wood = new T.Mesh(new T.ConeGeometry(.023, .12, 12), new T.MeshStandardMaterial({ color: '#ccb38b' })); wood.rotation.z = Math.PI; wood.position.y = .08; stylus.add(wood);
  const graphite = new T.Mesh(new T.ConeGeometry(.008, .045, 10), new T.MeshStandardMaterial({ color: '#35372c' })); graphite.rotation.z = Math.PI; graphite.position.y = .022; stylus.add(graphite);
  const cap = new T.Mesh(new T.CylinderGeometry(.025, .025, .065, 12), new T.MeshStandardMaterial({ color: '#575e51', metalness: .4, roughness: .3 })); cap.position.y = .5925; stylus.add(cap);
  stylus.quaternion.setFromUnitVectors(UP, new T.Vector3(-.43, .88, .12).normalize());
  stylus.traverse(o => { if (o instanceof T.Mesh) o.castShadow = true; });
  const fly = new T.Group(); fly.rotation.x = -Math.PI / 2; fly.position.x = -.3; scene.add(fly);
  let disposed = false; let animation = 0; let loaded = false;
  const joints: Record<string, T.Group> = {};
  const maps = flySurfaceMaps();
  const wingRest: Record<string, T.Quaternion> = {};
  const cleanup = () => { disposed = true; cancelAnimationFrame(animation); observer.disconnect(); controls.dispose(); scene.traverse(o => { if (o instanceof T.Mesh || o instanceof T.LineSegments || o instanceof T.Points) { o.geometry.dispose(); for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.dispose(); } }); maps.dispose(); paperTexture.dispose(); environment.dispose(); renderer.dispose(); renderer.domElement.remove(); };
  const assetPromise = (async () => {
    const response = await fetch('/models/fly/rig.json'); if (!response.ok) throw new Error('Fly rig unavailable'); const data: Rig = await response.json();
    const loader = new STLLoader(); const names = [...new Set(Object.keys(data.rig).map(n => n.startsWith('r') ? `l${n.slice(1)}` : n))];
    const loadedGeometry = await Promise.all(names.map(async n => [n, await loader.loadAsync(`/models/fly/${n}.stl`)] as const));
    if (disposed) { loadedGeometry.forEach(([, g]) => g.dispose()); return; }
    const geometries = Object.fromEntries(loadedGeometry);
    const amber = new T.MeshStandardMaterial({ color: '#8bb9a3', roughness: .58, metalness: .03 });
    const legMaterial = new T.MeshStandardMaterial({ color: '#e0a13c', roughness: .32, metalness: .18, bumpMap: maps.cuticle, bumpScale: .0014 });
    const eyeMaterial = new T.MeshPhysicalMaterial({ color: '#c53e29', roughness: .22, clearcoat: .8, bumpMap: maps.facets, bumpScale: .004 });
    const wingMaterial = new T.MeshPhysicalMaterial({ color: '#d5ded0', map: maps.veins, transparent: true, opacity: .36, metalness: .02, roughness: .36, side: T.DoubleSide, depthWrite: false, iridescence: .16, iridescenceIOR: 1.25 });
    Object.assign(joints, createJointRig(data, fly));
    for (const name of Object.keys(data.rig)) {
      const group = joints[name];
      const source = name.startsWith('r') ? `l${name.slice(1)}` : name;
      const raw = geometries[source].clone(); raw.deleteAttribute('normal');
      const geometry = mergeVertices(raw, .0000001); raw.dispose();
      geometry.scale(1000, name.startsWith('r') ? -1000 : 1000, 1000);
      if (name.startsWith('r')) { const index = geometry.index!; for (let i = 0; i < index.count; i += 3) { const a = index.getX(i); index.setX(i, index.getX(i + 2)); index.setX(i + 2, a); } }
      geometry.computeVertexNormals();
      if (/^c_|eye/.test(name)) softenSurface(geometry);
      surfaceUV(geometry, name.includes('wing'), name.startsWith('r'));
      let material: T.Material = name.includes('eye') ? eyeMaterial : name.includes('wing') ? wingMaterial : name.startsWith('c_') ? amber : legMaterial;
      if (name.endsWith('_tibia')) material = new T.MeshStandardMaterial({ color: '#bd8c75', roughness: .65, bumpMap: maps.cuticle, bumpScale: .0014 });
      if (/tarsus|arista|funiculus/.test(name)) material = new T.MeshStandardMaterial({ color: '#647c86', roughness: .63, bumpMap: maps.cuticle, bumpScale: .001 });
      if (name.includes('haltere')) material = new T.MeshStandardMaterial({ color: '#d3a36c', roughness: .58 });
      if (name.includes('abdomen')) material = new T.MeshStandardMaterial({ color: name === 'c_abdomen6' ? '#433321' : '#856137', roughness: .52, metalness: .1 });
      if (name.startsWith('c_') && !/rostrum|haustellum/.test(name)) {
        geometry.computeBoundingBox(); const bounds = geometry.boundingBox!;
        const p = geometry.getAttribute('position'), colors: number[] = [];
        for (let i = 0; i < p.count; i++) {
          const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
          const u = (x - bounds.min.x) / (bounds.max.x - bounds.min.x);
          const band = name.includes('abdomen') && u < .23;
          const stripe = name === 'c_thorax' ? Math.exp(-Math.pow((Math.abs(y) - .12) / .085, 2)) * .30 : 0;
          const color = new T.Color(band ? '#496d85' : name.includes('abdomen') ? '#e0a449' : name === 'c_head' ? '#b3c99a' : '#299c88');
          if (name === 'c_thorax') color.lerp(new T.Color('#839bc5'), Math.max(0, (z - bounds.min.z) / (bounds.max.z - bounds.min.z)) * .46);
          color.multiplyScalar(.98 - stripe + .02 * Math.sin(x * 321 + y * 733 + z * 519)); colors.push(...color.toArray());
        }
        geometry.setAttribute('color', new T.Float32BufferAttribute(colors, 3));
        material = new T.MeshPhysicalMaterial({ vertexColors: true, roughness: .30, clearcoat: .7, clearcoatRoughness: .24, metalness: .15, bumpMap: maps.cuticle, bumpScale: .002 });
      }
      const mesh = new T.Mesh(geometry, material); mesh.castShadow = !name.includes('wing'); mesh.receiveShadow = true; group.add(mesh);
      if (name.includes('wing')) wingRest[name] = group.quaternion.clone();
      // Fine cuticle bristles, sampled from actual mesh surfaces (deterministic).
      if (/thorax|head|abdomen|tibia|trochanterfemur/.test(name)) {
        const pos = geometry.getAttribute('position'), normal = geometry.getAttribute('normal'), points: number[] = [];
        const step = name.startsWith('c_') ? 93 : 231;
        for (let i = 0; i < pos.count; i += step) { const p = new T.Vector3().fromBufferAttribute(pos, i), n = new T.Vector3().fromBufferAttribute(normal, i); points.push(...p.toArray(), ...p.addScaledVector(n, name.startsWith('c_') ? .035 : .055).toArray()); }
        const hairs = new T.LineSegments(new T.BufferGeometry().setAttribute('position', new T.Float32BufferAttribute(points, 3)), new T.LineBasicMaterial({ color: '#3f6c5d', transparent: true, opacity: .28 })); group.add(hairs);
      }
    }
    Object.values(geometries).forEach(g => g.dispose());
    // Five planted support legs stay outside the body; only the right foreleg draws.
    for (const side of ['lf', 'lm', 'lh', 'rm', 'rh']) plantLeg(joints, side);
    // The fixed coxa connects the rendered anatomy to the reduced physical foreleg base.
    const base = new T.Vector3(.16, 1.07, .514);
    aimJoint(joints.rf_coxa, joints.rf_trochanterfemur.position, base.sub(joints.rf_coxa.getWorldPosition(new T.Vector3())));
    loaded = true; ready();
  })().catch(error => { if (!disposed) fail(String(error)); });
  let lastRun = -1; let previous: T.Vector2 | null = null; let lastTime = 0; let viewRevision = 0; let wingAmount = 0;
  const pen = new T.Vector3(1.25, 1.13, .15);
  const tick = (time: number) => {
    if (disposed) return;
    const dt = Math.min((time - lastTime) / 1000, .05); lastTime = time;
    if (live.run !== lastRun) { clearPaper(); paperTexture.needsUpdate = true; previous = null; lastRun = live.run; }
    if (live.resetView !== viewRevision) { applyCameraPreset(); viewRevision = live.resetView; }
    controls.update();
    const physical = live.physical;
    if (physical) pen.set(physical.tip[0], physical.tip[2] - .009, -physical.tip[1]);
    else pen.lerp(new T.Vector3(1.18, 1.15, .05), 1 - Math.exp(-dt * 24));
    stylus.position.copy(pen);
    for (const sample of live.ink.splice(0)) {
      if (!sample.contact || !sample.drawing) { previous = null; continue; }
      const p = new T.Vector2((sample.tip[0] - 1.55) / 1.15 * 1024 + 512, -sample.tip[1] / 1.15 * 1024 + 512);
      if (previous) { context.beginPath(); context.moveTo(previous.x, previous.y); context.lineTo(p.x, p.y); context.lineWidth = 5.2; context.strokeStyle = '#252b21'; context.lineCap = 'round'; context.lineJoin = 'round'; context.stroke(); paperTexture.needsUpdate = true; }
      previous = p;
    }
    if (loaded && physical) applyPhysicalPose(joints, stylus, physical);
    wingAmount += ((live.wings ? 1 : 0) - wingAmount) * (1 - Math.exp(-dt * 8));
    if (loaded) for (const name of ['l_wing', 'r_wing']) {
      if (!wingRest[name]) continue;
      const sign = name.startsWith('l') ? 1 : -1;
      // Separate, shallow-V resting wings; spread before applying the neural stroke.
      const spread = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 0, 1), -sign * (.42 + wingAmount * .7));
      const stroke = new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), sign * wingAmount * live.wing * .55);
      joints[name].quaternion.copy(stroke).multiply(spread).multiply(wingRest[name]);
    }
    renderer.render(scene, camera); animation = requestAnimationFrame(tick);
  };
  animation = requestAnimationFrame(tick);
  // Return synchronously after setup so React can dispose during asset loading.
  void assetPromise;
  return cleanup;
}
