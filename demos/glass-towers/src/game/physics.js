import RAPIER from "@dimforge/rapier3d-compat";
import { PEDESTAL } from "./config.js";

export const FIXED_TIME_STEP = 1 / 60;

let initialization;

export async function initializePhysicsEngine() {
  initialization ??= RAPIER.init();
  await initialization;
  return {
    backend: "rapier-wasm",
    version: RAPIER.version(),
  };
}

export function createPhysicsWorld() {
  const world = new RAPIER.World({ x: 0, y: -9.82, z: 0 });
  world.timestep = FIXED_TIME_STEP;
  const eventQueue = new RAPIER.EventQueue(true);

  const body = world.createRigidBody(
    RAPIER.RigidBodyDesc.fixed().setTranslation(0, -PEDESTAL.height / 2, 0),
  );
  const pedestalRadius = 0.08;
  const collider = world.createCollider(
    RAPIER.ColliderDesc.roundCuboid(
      PEDESTAL.width / 2 - pedestalRadius,
      PEDESTAL.height / 2 - pedestalRadius,
      PEDESTAL.depth / 2 - pedestalRadius,
      pedestalRadius,
    )
      .setFriction(0.78)
      .setRestitution(0.006)
      .setFrictionCombineRule(RAPIER.CoefficientCombineRule.Max)
      .setRestitutionCombineRule(RAPIER.CoefficientCombineRule.Min),
    body,
  );

  return { world, eventQueue, pedestal: { body, collider } };
}

function createColliderDescriptor(definition) {
  const [width, height, depth] = definition.dimensions;
  if (definition.geometry === "cylinder") {
    return RAPIER.ColliderDesc.roundCylinder(height / 2 - 0.04, width / 2 - 0.04, 0.04);
  }
  const radius = Math.min(width, height, depth) * 0.08;
  return RAPIER.ColliderDesc.roundCuboid(
    width / 2 - radius,
    height / 2 - radius,
    depth / 2 - radius,
    radius,
  );
}

export function createPhysicsBody(world, definition) {
  const body = world.createRigidBody(
    RAPIER.RigidBodyDesc.dynamic()
      .setLinearDamping(0.22)
      .setAngularDamping(0.34)
      .setCanSleep(true)
      .setCcdEnabled(true),
  );
  const collider = world.createCollider(
    createColliderDescriptor(definition)
      .setTranslation(...definition.centerOfMass)
      .setMass(definition.mass)
      .setFriction(0.72)
      .setRestitution(0.008)
      .setFrictionCombineRule(RAPIER.CoefficientCombineRule.Max)
      .setRestitutionCombineRule(RAPIER.CoefficientCombineRule.Min)
      .setActiveEvents(RAPIER.ActiveEvents.COLLISION_EVENTS),
    body,
  );
  return { body, collider };
}

export function vectorLengthSquared(vector) {
  return vector.x ** 2 + vector.y ** 2 + vector.z ** 2;
}

export function bodyPosition(body) {
  return body.translation();
}

export function bodyLinearVelocity(body) {
  return body.linvel();
}

export function bodyAngularVelocity(body) {
  return body.angvel();
}

export function bodySpeed(body) {
  return Math.sqrt(vectorLengthSquared(bodyLinearVelocity(body)));
}
