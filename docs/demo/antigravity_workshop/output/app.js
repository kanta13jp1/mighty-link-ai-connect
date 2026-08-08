const filterButtons = [...document.querySelectorAll(".filter-button")];
const cards = [...document.querySelectorAll(".agent-card")];
const selectButtons = [...document.querySelectorAll(".select-button")];
const resultCount = document.querySelector("#result-count");
const selectionCount = document.querySelector("#selection-count");
const selectionNames = document.querySelector("#selection-names");

const selectedAgents = new Set();

function updateFilter(filter) {
  let visible = 0;

  cards.forEach((card) => {
    const tags = card.dataset.tags.split(" ");
    const matches = filter === "all" || tags.includes(filter);
    card.hidden = !matches;
    if (matches) visible += 1;
  });

  filterButtons.forEach((button) => {
    const active = button.dataset.filter === filter;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  resultCount.textContent = `${visible}件表示`;
}

function updateComparison(message = "") {
  const selectedCards = cards.filter((card) => selectedAgents.has(card.dataset.agent));
  selectionCount.textContent = String(selectedCards.length);

  if (message) {
    selectionNames.innerHTML = `<p class="selection-alert">${message}</p>`;
    return;
  }

  if (selectedCards.length === 0) {
    selectionNames.innerHTML = "<p>製品カードから2つまで選べます。</p>";
    return;
  }

  selectionNames.innerHTML = selectedCards
    .map((card) => `<p><strong>${card.dataset.agent}</strong><span>${card.dataset.fit}</span></p>`)
    .join("");
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => updateFilter(button.dataset.filter));
});

selectButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest(".agent-card");
    const name = card.dataset.agent;
    const isSelected = selectedAgents.has(name);

    if (!isSelected && selectedAgents.size >= 2) {
      updateComparison("比較できるのは2製品までです。1つ外してから追加してください。");
      return;
    }

    if (isSelected) {
      selectedAgents.delete(name);
    } else {
      selectedAgents.add(name);
    }

    const nextState = !isSelected;
    button.setAttribute("aria-pressed", String(nextState));
    button.textContent = nextState ? "追加済み" : "比較に追加";
    card.classList.toggle("is-selected", nextState);
    updateComparison();
  });
});
