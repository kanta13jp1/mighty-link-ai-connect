import { GAME_LIMITS } from "./config.js";

function positionOf(body) {
  return typeof body.translation === "function" ? body.translation() : body.position;
}

function linearVelocityOf(body) {
  return typeof body.linvel === "function" ? body.linvel() : body.velocity;
}

function angularVelocityOf(body) {
  return typeof body.angvel === "function" ? body.angvel() : body.angularVelocity;
}

function lengthSquared(vector) {
  if (typeof vector.lengthSquared === "function") return vector.lengthSquared();
  return vector.x ** 2 + vector.y ** 2 + vector.z ** 2;
}

export function clampAim(value) {
  return Math.max(-GAME_LIMITS.aimRange, Math.min(GAME_LIMITS.aimRange, value));
}

export function isBodySettled(body) {
  if (typeof body.isSleeping === "function" && body.isSleeping()) return true;
  return (
    lengthSquared(linearVelocityOf(body)) <= GAME_LIMITS.stableLinearSpeed ** 2 &&
    lengthSquared(angularVelocityOf(body)) <= GAME_LIMITS.stableAngularSpeed ** 2
  );
}

export function isBodyLost(body) {
  const position = positionOf(body);
  const radialDistanceSquared = position.x ** 2 + position.z ** 2;
  return (
    position.y < GAME_LIMITS.failureY ||
    radialDistanceSquared > GAME_LIMITS.failureRadius ** 2
  );
}

export function structureHeight(pieces) {
  return pieces.reduce((highest, piece) => {
    const halfHeight = piece.definition.dimensions[1] / 2;
    return Math.max(highest, positionOf(piece.body).y + halfHeight);
  }, 0);
}

export function nextDropHeight(pieces) {
  return Math.max(3.3, structureHeight(pieces) + GAME_LIMITS.dropClearance);
}
