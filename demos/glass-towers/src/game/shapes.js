import * as THREE from "three/webgpu";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

export const SHAPE_CATALOG = Object.freeze([
  {
    id: "prism",
    name: "Soft prism",
    dimensions: [1.35, 1.05, 1.2],
    mass: 1.35,
    centerOfMass: [0, 0, 0],
    color: 0x8ad8d0,
    geometry: "rounded-box",
  },
  {
    id: "cantilever",
    name: "Cantilever",
    dimensions: [2.05, 0.62, 1.05],
    mass: 1.15,
    centerOfMass: [0.12, 0.02, 0],
    color: 0xf3a56f,
    geometry: "rounded-box",
  },
  {
    id: "monolith",
    name: "Monolith",
    dimensions: [0.88, 1.75, 0.9],
    mass: 1.42,
    centerOfMass: [-0.08, 0.08, 0.04],
    color: 0x8f9de8,
    geometry: "rounded-box",
  },
  {
    id: "lens",
    name: "Glass lens",
    dimensions: [1.45, 0.72, 1.45],
    mass: 1.08,
    centerOfMass: [0.1, 0, -0.06],
    color: 0xf0cf74,
    geometry: "cylinder",
  },
  {
    id: "keystone",
    name: "Keystone",
    dimensions: [1.55, 1.18, 0.82],
    mass: 1.28,
    centerOfMass: [-0.11, -0.04, 0],
    color: 0x91d17d,
    geometry: "rounded-box",
  },
]);

export function createGlassMaterial(color, environmentMap) {
  return new THREE.MeshPhysicalMaterial({
    color,
    metalness: 0,
    roughness: 0.08,
    transmission: 0.93,
    thickness: 0.68,
    ior: 1.47,
    transparent: true,
    opacity: 1,
    envMap: environmentMap,
    envMapIntensity: 1.7,
    clearcoat: 1,
    clearcoatRoughness: 0.08,
    attenuationColor: color,
    attenuationDistance: 2.4,
  });
}

function createGeometry(definition) {
  const [width, height, depth] = definition.dimensions;
  if (definition.geometry === "cylinder") {
    return new THREE.CylinderGeometry(width / 2, width / 2, height, 24, 1);
  }
  const radius = Math.min(width, height, depth) * 0.12;
  return new RoundedBoxGeometry(width, height, depth, 4, radius);
}

export function createVisual(definition, environmentMap) {
  const group = new THREE.Group();
  const mesh = new THREE.Mesh(
    createGeometry(definition),
    createGlassMaterial(definition.color, environmentMap),
  );
  mesh.position.set(...definition.centerOfMass);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);

  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(mesh.geometry, 26),
    new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.34 }),
  );
  edge.position.copy(mesh.position);
  group.add(edge);
  return group;
}

export function chooseNextShape(previousId, random = Math.random) {
  const options = SHAPE_CATALOG.filter((shape) => shape.id !== previousId);
  return options[Math.floor(random() * options.length) % options.length];
}
