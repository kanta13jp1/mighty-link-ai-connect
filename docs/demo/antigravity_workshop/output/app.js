const filterButtons = [...document.querySelectorAll(".filter-button")];
const sessionCards = [...document.querySelectorAll(".session-card")];
const resultCount = document.querySelector("#result-count");
const selectionCount = document.querySelector("#selection-count");
const selectionNames = document.querySelector("#selection-names");

function updateSelectionSummary() {
  const selected = sessionCards.filter((card) =>
    card.querySelector(".select-button").getAttribute("aria-pressed") === "true"
  );
  selectionCount.textContent = String(selected.length);
  selectionNames.textContent = selected.length
    ? selected.map((card) => card.dataset.session).join(" / ")
    : "まだ選択されていません。";
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    filterButtons.forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });

    let visible = 0;
    sessionCards.forEach((card) => {
      const show = filter === "all" || card.dataset.category === filter;
      card.hidden = !show;
      if (show) visible += 1;
    });
    resultCount.textContent = `${visible}件表示`;
  });
});

sessionCards.forEach((card) => {
  const button = card.querySelector(".select-button");
  button.addEventListener("click", () => {
    const selected = button.getAttribute("aria-pressed") === "true";
    button.setAttribute("aria-pressed", String(!selected));
    button.textContent = selected ? "参加候補に追加" : "追加済み";
    updateSelectionSummary();
  });
});

updateSelectionSummary();
