import { describe, expect, it } from "vitest";
import { GAME_LIMITS } from "../src/game/config.js";
import { clampAim, isBodyLost, isBodySettled, nextDropHeight, structureHeight } from "../src/game/rules.js";
import { SHAPE_CATALOG, chooseNextShape } from "../src/game/shapes.js";

function bodyAt({ x = 0, y = 0, z = 0, velocity = 0, angularVelocity = 0 } = {}) {
  return {
    position: { x, y, z },
    velocity: { lengthSquared: () => velocity ** 2 },
    angularVelocity: { lengthSquared: () => angularVelocity ** 2 },
  };
}

function rapierBodyAt({ x = 0, y = 0, z = 0, velocity = 0, angularVelocity = 0, sleeping = false } = {}) {
  return {
    translation: () => ({ x, y, z }),
    linvel: () => ({ x: velocity, y: 0, z: 0 }),
    angvel: () => ({ x: 0, y: angularVelocity, z: 0 }),
    isSleeping: () => sleeping,
  };
}

describe("Glass Towers rules", () => {
  it("clamps horizontal aiming to the playable rail", () => {
    expect(clampAim(99)).toBe(GAME_LIMITS.aimRange);
    expect(clampAim(-99)).toBe(-GAME_LIMITS.aimRange);
    expect(clampAim(0.7)).toBe(0.7);
  });

  it("distinguishes stable pieces from moving pieces", () => {
    expect(isBodySettled(bodyAt({ velocity: 0.04, angularVelocity: 0.03 }))).toBe(true);
    expect(isBodySettled(bodyAt({ velocity: 0.5 }))).toBe(false);
    expect(isBodySettled(rapierBodyAt({ sleeping: true, velocity: 4 }))).toBe(true);
    expect(isBodySettled(rapierBodyAt({ velocity: 0.5 }))).toBe(false);
  });

  it("ends a run below the pedestal or outside the arena", () => {
    expect(isBodyLost(bodyAt({ y: GAME_LIMITS.failureY - 0.01 }))).toBe(true);
    expect(isBodyLost(bodyAt({ x: GAME_LIMITS.failureRadius + 0.1 }))).toBe(true);
    expect(isBodyLost(bodyAt({ x: 1, y: 1 }))).toBe(false);
    expect(isBodyLost(rapierBodyAt({ y: GAME_LIMITS.failureY - 0.01 }))).toBe(true);
  });

  it("computes structure and next drop height from piece dimensions", () => {
    const pieces = [{
      body: bodyAt({ y: 2 }),
      definition: { dimensions: [1, 2, 1] },
    }];
    expect(structureHeight(pieces)).toBe(3);
    expect(nextDropHeight(pieces)).toBeCloseTo(5.8);
  });

  it("offers reusable shapes with varied sizes and centers of mass", () => {
    expect(SHAPE_CATALOG).toHaveLength(5);
    expect(new Set(SHAPE_CATALOG.map((shape) => shape.dimensions.join("x"))).size).toBe(5);
    expect(SHAPE_CATALOG.some((shape) => shape.centerOfMass.some((value) => value !== 0))).toBe(true);
    expect(chooseNextShape("prism", () => 0).id).not.toBe("prism");
  });
});
