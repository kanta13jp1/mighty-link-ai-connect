import "./style.css";
import { GlassTowersGame } from "./game/GlassTowersGame.js";
import { STORAGE_KEY } from "./game/config.js";

const elements = {
  canvas: document.querySelector("#game-canvas"),
  previewCanvas: document.querySelector("#preview-canvas"),
  score: document.querySelector("#score"),
  best: document.querySelector("#best-score"),
  height: document.querySelector("#height"),
  nextName: document.querySelector("#next-name"),
  engineLabel: document.querySelector("#engine-label"),
  loading: document.querySelector("#loading-state"),
  stateDot: document.querySelector("#state-dot"),
  stateLabel: document.querySelector("#state-label"),
  restartButton: document.querySelector("#restart-button"),
  playAgainButton: document.querySelector("#play-again-button"),
  gameOver: document.querySelector("#game-over"),
  finalScore: document.querySelector("#final-score"),
  finalHeight: document.querySelector("#final-height"),
  srStatus: document.querySelector("#sr-status"),
};

function readBestScore() {
  try {
    return Number.parseInt(localStorage.getItem(STORAGE_KEY) ?? "0", 10) || 0;
  } catch {
    return 0;
  }
}

function writeBestScore(value) {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    // The game remains playable when storage is disabled.
  }
}

function formatEngine(engine) {
  const renderer = engine.renderer === "webgpu" ? "WEBGPU" : "WEBGL 2";
  return `${renderer} / RAPIER WASM`;
}

async function bootstrap() {
  let bestScore = readBestScore();
  elements.best.textContent = String(bestScore).padStart(2, "0");

  try {
    const game = await GlassTowersGame.create({
      canvas: elements.canvas,
      previewCanvas: elements.previewCanvas,
    });

    function renderScore(snapshot) {
      elements.score.textContent = String(snapshot.score).padStart(2, "0");
      elements.height.textContent = snapshot.height.toFixed(1);
      if (snapshot.score > bestScore) {
        bestScore = snapshot.score;
        writeBestScore(bestScore);
        elements.best.textContent = String(bestScore).padStart(2, "0");
      }
    }

    game.addEventListener("scorechange", (event) => {
      renderScore(event.detail);
      if (event.detail.score > 0) {
        elements.srStatus.textContent = `Piece ${event.detail.score} is stable. Height ${event.detail.height.toFixed(1)} meters.`;
      }
    });

    game.addEventListener("nextchange", (event) => {
      elements.nextName.textContent = event.detail.definition.name;
    });

    game.addEventListener("statechange", (event) => {
      const labels = { aiming: "POSITION", falling: "SETTLING", gameover: "RUN ENDED" };
      elements.stateLabel.textContent = labels[event.detail.state];
      elements.stateDot.classList.toggle("is-falling", event.detail.state !== "aiming");
      if (event.detail.state !== "gameover") elements.gameOver.hidden = true;
    });

    game.addEventListener("gameover", (event) => {
      renderScore(event.detail);
      elements.finalScore.textContent = String(event.detail.score);
      elements.finalHeight.textContent = event.detail.height.toFixed(1);
      elements.gameOver.hidden = false;
      elements.playAgainButton.focus();
      elements.srStatus.textContent = `Run ended with ${event.detail.score} pieces.`;
    });

    function restart() {
      game.restart();
      renderScore(game.snapshot());
      elements.gameOver.hidden = true;
      elements.canvas.focus?.();
    }

    elements.restartButton.addEventListener("click", restart);
    elements.playAgainButton.addEventListener("click", restart);

    const initial = game.snapshot();
    renderScore(initial);
    elements.nextName.textContent = game.nextDefinition.name;
    elements.engineLabel.textContent = formatEngine(initial.engine);
    elements.loading.hidden = true;

    window.__GLASS_TOWERS__ = {
      snapshot: () => game.snapshot(),
      dropAt: (x) => game.debugDropAt(x),
      advance: (frames) => game.debugAdvance(frames),
      restart,
    };
  } catch (error) {
    console.error("Glass Towers failed to initialize", error);
    elements.engineLabel.textContent = "ENGINE UNAVAILABLE";
    elements.loading.textContent = "Unable to initialize the graphics or physics engine.";
    elements.loading.classList.add("is-error");
  }
}

bootstrap();
