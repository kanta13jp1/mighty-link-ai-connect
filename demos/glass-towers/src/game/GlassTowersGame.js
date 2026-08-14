import * as THREE from "three/webgpu";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { GAME_LIMITS, PEDESTAL } from "./config.js";
import {
  FIXED_TIME_STEP,
  bodyAngularVelocity,
  bodyLinearVelocity,
  bodyPosition,
  bodySpeed,
  createPhysicsBody,
  createPhysicsWorld,
  initializePhysicsEngine,
  vectorLengthSquared,
} from "./physics.js";
import { clampAim, isBodyLost, isBodySettled, nextDropHeight, structureHeight } from "./rules.js";
import { SHAPE_CATALOG, chooseNextShape, createVisual } from "./shapes.js";

export class GlassTowersGame extends EventTarget {
  constructor({ canvas, previewCanvas }) {
    super();
    this.canvas = canvas;
    this.previewCanvas = previewCanvas;
    this.clock = new THREE.Clock();
    this.pieces = [];
    this.effects = [];
    this.score = 0;
    this.height = 0;
    this.state = "aiming";
    this.aimX = 0;
    this.displayAimX = 0;
    this.stableFor = 0;
    this.cameraShake = 0;
    this.physicsAccumulator = 0;
    this.rendererBackend = "initializing";
    this.physicsInfo = { backend: "initializing", version: "" };
    this.disposed = false;
  }

  static async create(options) {
    const game = new GlassTowersGame(options);
    game.physicsInfo = await initializePhysicsEngine();
    await game.initialize();
    return game;
  }

  async initialize() {
    await this.setupRenderer();
    this.setupScene();
    this.setupPhysics();
    await this.setupPreview();
    this.bindInputs();

    this.currentDefinition = SHAPE_CATALOG[0];
    this.nextDefinition = chooseNextShape(this.currentDefinition.id);
    this.spawnAimingPiece();
    this.updatePreview();
    this.resize();
    this.renderer.setAnimationLoop(this.animate);
  }

  async setupRenderer() {
    const params = new URLSearchParams(window.location.search);
    const forceWebGL = params.get("renderer") === "webgl2" || params.has("force-webgl");
    this.renderer = new THREE.WebGPURenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
      forceWebGL,
    });
    await this.renderer.init();
    this.rendererBackend = this.renderer.backend?.isWebGPUBackend ? "webgpu" : "webgl2";
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, GAME_LIMITS.maxPixelRatio));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.08;
  }

  setupScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xeceef2);
    this.scene.fog = new THREE.Fog(0xeceef2, 16, 32);

    this.camera = new THREE.PerspectiveCamera(38, 1, 0.1, 80);
    this.camera.position.set(8.6, 6.5, 11.2);
    this.cameraTarget = new THREE.Vector3(0, 1.8, 0);

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.environmentMap = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environment = this.environmentMap;
    pmrem.dispose();

    const key = new THREE.DirectionalLight(0xffffff, 4.4);
    key.position.set(4, 10, 6);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.left = -8;
    key.shadow.camera.right = 8;
    key.shadow.camera.top = 12;
    key.shadow.camera.bottom = -4;
    this.scene.add(key);

    const fill = new THREE.DirectionalLight(0x8bd8d0, 2.2);
    fill.position.set(-7, 5, -3);
    this.scene.add(fill);

    const rim = new THREE.PointLight(0xf0a477, 44, 22, 1.8);
    rim.position.set(5, 3, -5);
    this.scene.add(rim);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(18, 64),
      new THREE.MeshStandardMaterial({ color: 0xe2e4e8, roughness: 0.72, metalness: 0.04 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -1.16;
    floor.receiveShadow = true;
    this.scene.add(floor);

    const floorRing = new THREE.Mesh(
      new THREE.RingGeometry(5.7, 5.73, 96),
      new THREE.MeshBasicMaterial({ color: 0xb8bdc3, transparent: true, opacity: 0.62, side: THREE.DoubleSide }),
    );
    floorRing.rotation.x = -Math.PI / 2;
    floorRing.position.y = -1.145;
    this.scene.add(floorRing);

    const pedestal = new THREE.Mesh(
      new RoundedBoxGeometry(PEDESTAL.width, PEDESTAL.height, PEDESTAL.depth, 4, 0.14),
      new THREE.MeshPhysicalMaterial({
        color: 0x20262a,
        roughness: 0.25,
        metalness: 0.62,
        clearcoat: 0.72,
        clearcoatRoughness: 0.16,
      }),
    );
    pedestal.position.y = -PEDESTAL.height / 2;
    pedestal.castShadow = true;
    pedestal.receiveShadow = true;
    this.scene.add(pedestal);

    const topPlate = new THREE.Mesh(
      new RoundedBoxGeometry(PEDESTAL.width - 0.18, 0.05, PEDESTAL.depth - 0.18, 3, 0.08),
      new THREE.MeshPhysicalMaterial({
        color: 0xced4d8,
        metalness: 0.18,
        roughness: 0.12,
        clearcoat: 1,
      }),
    );
    topPlate.position.y = 0.026;
    topPlate.receiveShadow = true;
    this.scene.add(topPlate);

    this.guide = new THREE.Mesh(
      new THREE.RingGeometry(0.31, 0.36, 40),
      new THREE.MeshBasicMaterial({ color: 0xe8593c, transparent: true, opacity: 0.68, side: THREE.DoubleSide }),
    );
    this.guide.rotation.x = -Math.PI / 2;
    this.guide.position.y = 0.065;
    this.scene.add(this.guide);
  }

  setupPhysics() {
    const physics = createPhysicsWorld();
    this.world = physics.world;
    this.eventQueue = physics.eventQueue;
    this.pedestalBody = physics.pedestal.body;
  }

  async setupPreview() {
    this.previewRenderer = new THREE.WebGPURenderer({
      canvas: this.previewCanvas,
      alpha: true,
      antialias: true,
      forceWebGL: this.rendererBackend !== "webgpu",
    });
    await this.previewRenderer.init();
    this.previewRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    this.previewRenderer.outputColorSpace = THREE.SRGBColorSpace;
    this.previewRenderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.previewRenderer.toneMappingExposure = 1.18;
    this.previewScene = new THREE.Scene();
    this.previewScene.environment = this.environmentMap;
    this.previewCamera = new THREE.PerspectiveCamera(32, 1, 0.1, 20);
    this.previewCamera.position.set(2.6, 1.9, 3.4);
    this.previewCamera.lookAt(0, 0, 0);
    this.previewScene.add(new THREE.HemisphereLight(0xffffff, 0x667077, 3.4));
  }

  bindInputs() {
    this.onPointerMove = (event) => {
      if (this.state !== "aiming") return;
      const rect = this.canvas.getBoundingClientRect();
      const normalized = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.setAim(normalized * GAME_LIMITS.aimRange);
    };
    this.onPointerDown = (event) => {
      if (event.button !== undefined && event.button !== 0) return;
      this.onPointerMove(event);
      this.drop();
    };
    this.onKeyDown = (event) => {
      if (event.code === "ArrowLeft" || event.code === "KeyA") {
        event.preventDefault();
        this.setAim(this.aimX - 0.28);
      }
      if (event.code === "ArrowRight" || event.code === "KeyD") {
        event.preventDefault();
        this.setAim(this.aimX + 0.28);
      }
      if (event.code === "Space" || event.code === "Enter") {
        event.preventDefault();
        this.drop();
      }
      if (event.code === "KeyR") this.restart();
    };
    this.onResize = () => this.resize();
    this.canvas.addEventListener("pointermove", this.onPointerMove);
    this.canvas.addEventListener("pointerdown", this.onPointerDown);
    window.addEventListener("keydown", this.onKeyDown);
    window.addEventListener("resize", this.onResize);
  }

  setAim(value) {
    if (this.state !== "aiming") return;
    this.aimX = clampAim(value);
  }

  spawnAimingPiece() {
    if (this.aimingVisual) this.scene.remove(this.aimingVisual);
    this.aimX = 0;
    this.displayAimX = 0;
    this.aimingVisual = createVisual(this.currentDefinition, this.environmentMap);
    this.aimingVisual.position.set(0, nextDropHeight(this.pieces), 0);
    this.scene.add(this.aimingVisual);
    this.guide.visible = true;
    this.state = "aiming";
    this.emitState();
  }

  updatePreview() {
    if (this.previewVisual) this.previewScene.remove(this.previewVisual);
    this.previewVisual = createVisual(this.nextDefinition, this.environmentMap);
    const maxDimension = Math.max(...this.nextDefinition.dimensions);
    this.previewVisual.scale.setScalar(1.6 / maxDimension);
    this.previewScene.add(this.previewVisual);
    this.dispatchEvent(new CustomEvent("nextchange", { detail: { definition: this.nextDefinition } }));
  }

  drop() {
    if (this.state !== "aiming" || !this.aimingVisual) return false;
    this.state = "falling";
    this.emitState();
    this.guide.visible = false;

    const visual = this.aimingVisual;
    this.aimingVisual = null;
    const { body, collider } = createPhysicsBody(this.world, this.currentDefinition);
    body.setTranslation({ x: this.displayAimX, y: visual.position.y, z: 0 }, true);
    const orientation = new THREE.Quaternion().setFromEuler(new THREE.Euler(
      0,
      (this.score % 5) * 0.08,
      (this.score % 2 ? 1 : -1) * 0.006,
    ));
    body.setRotation(orientation, true);
    body.setAngvel({ x: 0, y: 0.025 * (this.score % 2 ? 1 : -1), z: 0.008 }, true);

    this.activePiece = {
      body,
      collider,
      visual,
      definition: this.currentDefinition,
      scored: false,
      impactHandled: false,
      preStepSpeed: 0,
    };
    this.pieces.push(this.activePiece);
    this.stableFor = 0;
    return true;
  }

  handleImpact(piece, speed) {
    if (piece.impactHandled) return;
    if (speed < 1.1) return;
    piece.impactHandled = true;
    this.cameraShake = Math.min(0.18, speed * 0.018);
    this.createImpactEffect(bodyPosition(piece.body), speed);
    if (navigator.vibrate) navigator.vibrate(Math.min(24, Math.round(speed * 3)));
    this.dispatchEvent(new CustomEvent("impact", { detail: { speed } }));
  }

  createImpactEffect(position, speed) {
    const mesh = new THREE.Mesh(
      new THREE.RingGeometry(0.22, 0.28, 48),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.72, side: THREE.DoubleSide, depthWrite: false }),
    );
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(position.x, Math.max(0.08, position.y - 0.5), position.z);
    this.scene.add(mesh);
    this.effects.push({ mesh, age: 0, duration: 0.48, strength: Math.min(2, speed / 3) });
  }

  scoreActivePiece() {
    if (!this.activePiece || this.activePiece.scored) return;
    this.activePiece.scored = true;
    this.score += 1;
    this.height = structureHeight(this.pieces);
    this.dispatchEvent(new CustomEvent("scorechange", { detail: this.snapshot() }));
    this.currentDefinition = this.nextDefinition;
    this.nextDefinition = chooseNextShape(this.currentDefinition.id);
    this.updatePreview();
    this.activePiece = null;
    window.setTimeout(() => {
      if (this.state !== "gameover") this.spawnAimingPiece();
    }, 260);
  }

  endRun() {
    if (this.state === "gameover") return;
    this.state = "gameover";
    this.guide.visible = false;
    if (this.aimingVisual) {
      this.scene.remove(this.aimingVisual);
      this.aimingVisual = null;
    }
    this.height = structureHeight(this.pieces.filter((piece) => !isBodyLost(piece.body)));
    this.emitState();
    this.dispatchEvent(new CustomEvent("gameover", { detail: this.snapshot() }));
  }

  restart() {
    for (const piece of this.pieces) {
      this.world.removeRigidBody(piece.body);
      this.scene.remove(piece.visual);
    }
    for (const effect of this.effects) this.scene.remove(effect.mesh);
    this.pieces = [];
    this.effects = [];
    this.activePiece = null;
    this.score = 0;
    this.height = 0;
    this.stableFor = 0;
    this.cameraShake = 0;
    this.physicsAccumulator = 0;
    this.currentDefinition = SHAPE_CATALOG[0];
    this.nextDefinition = chooseNextShape(this.currentDefinition.id);
    this.updatePreview();
    this.spawnAimingPiece();
    this.dispatchEvent(new CustomEvent("scorechange", { detail: this.snapshot() }));
  }

  emitState() {
    this.dispatchEvent(new CustomEvent("statechange", { detail: this.snapshot() }));
  }

  drainCollisionEvents() {
    this.eventQueue.drainCollisionEvents((first, second, started) => {
      if (!started) return;
      const piece = this.pieces.find(
        (candidate) => candidate.collider.handle === first || candidate.collider.handle === second,
      );
      if (piece) this.handleImpact(piece, piece.preStepSpeed);
    });
  }

  stepPhysics() {
    for (const piece of this.pieces) piece.preStepSpeed = bodySpeed(piece.body);
    this.world.step(this.eventQueue);
    this.drainCollisionEvents();

    for (const piece of this.pieces) {
      piece.visual.position.copy(bodyPosition(piece.body));
      piece.visual.quaternion.copy(piece.body.rotation());
      if (isBodyLost(piece.body)) {
        this.endRun();
        return;
      }
    }

    if (this.state === "falling" && this.activePiece) {
      if (isBodySettled(this.activePiece.body)) {
        this.stableFor += FIXED_TIME_STEP;
        if (this.stableFor >= GAME_LIMITS.stableSeconds) this.scoreActivePiece();
      } else {
        this.stableFor = 0;
      }
    }
  }

  updatePhysics(delta) {
    if (this.pieces.length === 0) return;
    this.physicsAccumulator = Math.min(this.physicsAccumulator + delta, FIXED_TIME_STEP * 4);
    while (this.physicsAccumulator >= FIXED_TIME_STEP && this.state !== "gameover") {
      this.stepPhysics();
      this.physicsAccumulator -= FIXED_TIME_STEP;
    }
  }

  updateVisuals(delta, elapsed) {
    if (this.aimingVisual) {
      this.displayAimX = THREE.MathUtils.damp(this.displayAimX, this.aimX, 11, delta);
      this.aimingVisual.position.x = this.displayAimX;
      this.aimingVisual.position.y = nextDropHeight(this.pieces) + Math.sin(elapsed * 2.1) * 0.04;
      this.aimingVisual.rotation.y = Math.sin(elapsed * 0.62) * 0.16;
      this.guide.position.x = this.displayAimX;
    }

    for (let index = this.effects.length - 1; index >= 0; index -= 1) {
      const effect = this.effects[index];
      effect.age += delta;
      const progress = Math.min(1, effect.age / effect.duration);
      effect.mesh.scale.setScalar(1 + progress * 4.8 * effect.strength);
      effect.mesh.material.opacity = (1 - progress) * 0.72;
      if (progress >= 1) {
        this.scene.remove(effect.mesh);
        this.effects.splice(index, 1);
      }
    }

    if (this.previewVisual) {
      this.previewVisual.rotation.y += delta * 0.8;
      this.previewVisual.rotation.x = Math.sin(elapsed * 0.8) * 0.08;
    }

    const currentHeight = Math.max(0, structureHeight(this.pieces));
    const desiredTargetY = Math.max(1.45, currentHeight * 0.5 + 0.85);
    this.cameraTarget.y = THREE.MathUtils.damp(this.cameraTarget.y, desiredTargetY, 3.2, delta);
    const desiredCameraY = 6.2 + Math.max(0, currentHeight - 3) * 0.34;
    const desiredCameraZ = 11.2 + Math.max(0, currentHeight - 5) * 0.2;
    this.camera.position.y = THREE.MathUtils.damp(this.camera.position.y, desiredCameraY, 2.6, delta);
    this.camera.position.z = THREE.MathUtils.damp(this.camera.position.z, desiredCameraZ, 2.6, delta);
    this.camera.position.x = 8.6 + Math.sin(elapsed * 0.09) * 0.22;
    if (this.cameraShake > 0.001) {
      this.camera.position.x += (Math.random() - 0.5) * this.cameraShake;
      this.camera.position.y += (Math.random() - 0.5) * this.cameraShake;
      this.cameraShake *= 0.84;
    }
    this.camera.lookAt(this.cameraTarget);
  }

  animate = () => {
    if (this.disposed) return;
    const delta = Math.min(this.clock.getDelta(), 0.05);
    const elapsed = this.clock.elapsedTime;
    this.updatePhysics(delta);
    this.updateVisuals(delta, elapsed);
    this.renderer.render(this.scene, this.camera);
    this.previewRenderer.render(this.previewScene, this.previewCamera);
  };

  resize() {
    const width = Math.max(1, this.canvas.clientWidth);
    const height = Math.max(1, this.canvas.clientHeight);
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    const previewSize = Math.max(1, this.previewCanvas.clientWidth || 112);
    this.previewRenderer.setSize(previewSize, previewSize, false);
    this.previewCamera.aspect = 1;
    this.previewCamera.updateProjectionMatrix();
  }

  snapshot() {
    return {
      state: this.state,
      score: this.score,
      height: Number(this.height.toFixed(2)),
      aimX: Number(this.aimX.toFixed(2)),
      displayAimX: Number(this.displayAimX.toFixed(2)),
      pieces: this.pieces.length,
      current: this.currentDefinition?.id ?? null,
      next: this.nextDefinition?.id ?? null,
      activeBody: this.activePiece ? {
        position: {
          x: Number(bodyPosition(this.activePiece.body).x.toFixed(2)),
          y: Number(bodyPosition(this.activePiece.body).y.toFixed(2)),
          z: Number(bodyPosition(this.activePiece.body).z.toFixed(2)),
        },
        speed: Number(Math.sqrt(vectorLengthSquared(bodyLinearVelocity(this.activePiece.body))).toFixed(3)),
        angularSpeed: Number(Math.sqrt(vectorLengthSquared(bodyAngularVelocity(this.activePiece.body))).toFixed(3)),
        sleepState: this.activePiece.body.isSleeping() ? "sleeping" : "awake",
        stableFor: Number(this.stableFor.toFixed(2)),
      } : null,
      engine: {
        renderer: this.rendererBackend,
        physics: this.physicsInfo.backend,
        physicsVersion: this.physicsInfo.version,
        webgpuAvailable: Boolean(navigator.gpu),
      },
    };
  }

  debugDropAt(x) {
    if (this.state !== "aiming") return false;
    this.aimX = clampAim(x);
    this.displayAimX = this.aimX;
    if (this.aimingVisual) this.aimingVisual.position.x = this.aimX;
    return this.drop();
  }

  debugAdvance(frames = 360) {
    const steps = Math.max(1, Math.min(1200, Math.trunc(frames)));
    for (let index = 0; index < steps; index += 1) {
      if (this.state === "gameover" || (this.score > 0 && !this.activePiece)) break;
      this.stepPhysics();
    }
    return this.snapshot();
  }

  dispose() {
    this.disposed = true;
    this.canvas.removeEventListener("pointermove", this.onPointerMove);
    this.canvas.removeEventListener("pointerdown", this.onPointerDown);
    window.removeEventListener("keydown", this.onKeyDown);
    window.removeEventListener("resize", this.onResize);
    this.renderer.setAnimationLoop(null);
    this.renderer.dispose();
    this.previewRenderer.dispose();
    this.eventQueue.free();
    this.world.free();
  }
}
