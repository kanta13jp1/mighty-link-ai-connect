(() => {
  "use strict";

  const products = Array.isArray(window.PRODUCT_DATA) ? window.PRODUCT_DATA : [];
  const selectedIds = new Set();
  let activeScenario = "all";
  let searchQuery = "";

  const scenarios = {
    all: {
      ids: products.map((product) => product.id),
      message: "5製品を表示しています。カードから最大2製品を詳細比較できます。"
    },
    code: {
      ids: ["codex", "claude-code", "kiro", "antigravity"],
      message: "コード実装は、横断的な開発ならCodex、CLI中心ならClaude Code、仕様駆動ならKiro、画面検証まで一体化するならAntigravityが候補です。"
    },
    knowledge: {
      ids: ["claude-cowork"],
      message: "資料、表計算、メール、カレンダー、定期レポートをまたぐ仕事はClaude Coworkが中心候補です。"
    },
    spec: {
      ids: ["kiro", "codex", "claude-code"],
      message: "仕様を正式な工程として残すならKiro。既存の設計書やテストを基準に実装するならCodexとClaude Codeも候補です。"
    },
    browser: {
      ids: ["antigravity", "codex", "claude-cowork"],
      message: "Web制作と画面証拠はAntigravity、アプリ内Browserを含む開発はCodex、業務Web操作はClaude Coworkが候補です。"
    },
    automation: {
      ids: ["codex", "claude-code", "kiro", "antigravity", "claude-cowork"],
      message: "SDK/CIはCodexとClaude Code、仕様とHooksはKiro、Browserを含むSDK実演はAntigravity、定期業務はClaude Coworkが向きます。"
    }
  };

  const productGrid = document.getElementById("product-grid");
  const emptyState = document.getElementById("empty-state");
  const searchInput = document.getElementById("product-search");
  const scenarioResult = document.getElementById("scenario-result");
  const selectionCount = document.getElementById("selection-count");
  const compareStatus = document.getElementById("compare-status");
  const comparisonEmpty = document.getElementById("comparison-empty");
  const comparisonTableWrap = document.getElementById("comparison-table-wrap");
  const comparisonHead = document.getElementById("comparison-head");
  const comparisonBody = document.getElementById("comparison-body");
  const clearComparison = document.getElementById("clear-comparison");
  const sourceLedger = document.getElementById("source-ledger");
  const sourceCount = document.getElementById("source-count");

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function externalLink(label, url, className) {
    const link = element("a", className, label);
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  }

  function createMediaLink(kind, item) {
    const link = externalLink("", item.url, "media-link");
    link.append(
      element("span", "", kind),
      element("strong", "", item.title),
      element("small", "", `${item.date}${item.channel ? ` / ${item.channel}` : ""}`)
    );
    return link;
  }

  function createProductCard(product) {
    const card = element("article", "product-card");
    card.dataset.product = product.id;
    card.dataset.search = [
      product.name,
      product.vendor,
      product.oneLine,
      product.bestFor,
      product.notIdealFor,
      ...product.tags,
      ...Object.values(product.comparison)
    ].join(" ").toLowerCase();

    const head = element("div", "product-card-head");
    const iconWrap = element("div", "product-icon-wrap");
    const icon = element("img", "product-icon");
    icon.src = product.icon;
    icon.alt = `${product.name} 公式アイコン`;
    icon.width = 42;
    icon.height = 42;
    icon.loading = "lazy";
    iconWrap.append(icon);

    const meta = element("div", "product-meta");
    meta.append(element("p", "vendor", product.vendor), element("h3", "product-name", product.name));

    const release = element("a", "release-badge");
    release.href = product.release.url;
    release.target = "_blank";
    release.rel = "noopener noreferrer";
    release.setAttribute("aria-label", `${product.name} ${product.release.version} の公式更新情報`);
    release.append(
      element("strong", "", product.release.version),
      element("span", "", `${product.release.label} / ${product.release.date}`)
    );
    head.append(iconWrap, meta, release);

    const summary = element("p", "product-summary", product.oneLine);

    const fitGrid = element("div", "fit-grid");
    const bestFit = element("div", "fit-item");
    bestFit.append(element("span", "fit-label", "選ぶ理由"), element("p", "", product.bestFor));
    const caution = element("div", "fit-item is-caution");
    caution.append(element("span", "fit-label", "別候補も見る条件"), element("p", "", product.notIdealFor));
    fitGrid.append(bestFit, caution);

    const update = element("div", "update-block");
    update.append(
      element("span", "update-kicker", `LATEST UPDATE / ${product.latestUpdate.date}`),
      element("h4", "", product.latestUpdate.title),
      element("p", "", product.latestUpdate.summary)
    );

    const media = element("div", "media-grid");
    media.append(
      createMediaLink("最新公式動画", product.latestVideo),
      createMediaLink("最新公式ブログ", product.latestBlog)
    );

    const details = element("details", "card-details");
    details.append(element("summary", "", "実務比較の要点"));
    const detailList = element("ul", "detail-list");
    ["操作面", "持続指示", "能力拡張", "MCP・連携", "証拠とレビュー", "安全境界", "価格・利用枠"].forEach((field) => {
      const item = element("li", "");
      item.append(element("strong", "", field), element("span", "", product.comparison[field]));
      detailList.append(item);
    });
    details.append(detailList);

    const actions = element("div", "card-actions");
    const compareButton = element("button", "compare-button", "比較に追加");
    compareButton.type = "button";
    compareButton.dataset.productId = product.id;
    compareButton.setAttribute("aria-pressed", "false");
    compareButton.setAttribute("aria-label", `${product.name}を詳細比較に追加`);
    compareButton.addEventListener("click", () => toggleSelection(product.id));

    const links = element("div", "official-links");
    links.append(
      externalLink("公式Docs", product.sources[0].url),
      externalLink("更新履歴", product.release.url)
    );
    actions.append(compareButton, links);

    card.append(head, summary, fitGrid, update, media, details, actions);
    return card;
  }

  function renderProducts() {
    productGrid.replaceChildren(...products.map(createProductCard));
    applyFilters();
  }

  function applyFilters() {
    const allowed = new Set(scenarios[activeScenario].ids);
    let visibleCount = 0;

    document.querySelectorAll(".product-card").forEach((card) => {
      const matchesScenario = allowed.has(card.dataset.product);
      const matchesSearch = !searchQuery || card.dataset.search.includes(searchQuery);
      const visible = matchesScenario && matchesSearch;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    emptyState.hidden = visibleCount !== 0;
    const baseMessage = scenarios[activeScenario].message;
    scenarioResult.textContent = searchQuery
      ? `${baseMessage} 検索結果は${visibleCount}製品です。`
      : baseMessage;
  }

  function toggleSelection(productId) {
    if (selectedIds.has(productId)) {
      selectedIds.delete(productId);
      compareStatus.textContent = "比較候補から外しました。";
    } else if (selectedIds.size >= 2) {
      const current = [...selectedIds].map((id) => products.find((product) => product.id === id).name);
      compareStatus.textContent = `比較は最大2製品です。${current.join(" と ")}のどちらかを外してください。`;
      return;
    } else {
      selectedIds.add(productId);
      compareStatus.textContent = selectedIds.size === 1
        ? "1製品を選択しました。もう1製品を追加すると横並びで比較できます。"
        : "2製品を選択しました。13の実務軸で差を確認できます。";
    }

    updateSelectionUi();
  }

  function updateSelectionUi() {
    document.querySelectorAll(".product-card").forEach((card) => {
      const selected = selectedIds.has(card.dataset.product);
      card.classList.toggle("is-selected", selected);
      const button = card.querySelector(".compare-button");
      button.setAttribute("aria-pressed", String(selected));
      button.textContent = selected ? "比較から外す" : "比較に追加";
    });

    selectionCount.textContent = String(selectedIds.size);
    clearComparison.disabled = selectedIds.size === 0;
    renderComparison();
  }

  function renderComparison() {
    const selected = [...selectedIds]
      .map((id) => products.find((product) => product.id === id))
      .filter(Boolean);

    if (selected.length === 0) {
      comparisonEmpty.hidden = false;
      comparisonTableWrap.hidden = true;
      comparisonHead.replaceChildren();
      comparisonBody.replaceChildren();
      return;
    }

    comparisonEmpty.hidden = true;
    comparisonTableWrap.hidden = false;

    const headerRow = element("tr", "");
    headerRow.append(element("th", "", "比較軸"));
    selected.forEach((product) => {
      const heading = element("th", "");
      heading.scope = "col";
      const wrapper = element("div", "comparison-product");
      const icon = element("img", "");
      icon.src = product.icon;
      icon.alt = "";
      icon.width = 32;
      icon.height = 32;
      wrapper.append(icon, element("span", "", product.name));
      heading.append(wrapper);
      headerRow.append(heading);
    });
    comparisonHead.replaceChildren(headerRow);

    const fields = Object.keys(selected[0].comparison);
    const rows = fields.map((field) => {
      const row = element("tr", "");
      const label = element("th", "", field);
      label.scope = "row";
      row.append(label);
      selected.forEach((product) => row.append(element("td", "", product.comparison[field])));
      return row;
    });
    comparisonBody.replaceChildren(...rows);
  }

  function renderSourceLedger() {
    let total = 0;
    const rows = products.map((product) => {
      const row = element("article", "source-row");
      const productBlock = element("div", "source-product");
      const icon = element("img", "");
      icon.src = product.icon;
      icon.alt = "";
      icon.width = 38;
      icon.height = 38;
      const text = element("div", "");
      text.append(element("strong", "", product.name), element("span", "", `確認日 2026-08-13 / ${product.release.version}`));
      productBlock.append(icon, text);

      const links = element("div", "source-links");
      const allSources = [
        ...product.sources,
        {label: "最新更新", url: product.latestUpdate.url},
        {label: "最新動画", url: product.latestVideo.url},
        {label: "最新ブログ", url: product.latestBlog.url},
        {label: "アイコン配布元", url: product.iconSource}
      ];
      total += allSources.length;
      allSources.forEach((source) => {
        const link = externalLink(source.label, source.url);
        link.setAttribute("aria-label", `${product.name}: ${source.label}を開く`);
        links.append(link);
      });
      row.append(productBlock, links);
      return row;
    });

    sourceLedger.replaceChildren(...rows);
    sourceCount.textContent = `${total}件`;
  }

  document.querySelectorAll(".scenario-button").forEach((button) => {
    button.addEventListener("click", () => {
      activeScenario = button.dataset.scenario;
      document.querySelectorAll(".scenario-button").forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("is-active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
      applyFilters();
    });
  });

  searchInput.addEventListener("input", () => {
    searchQuery = searchInput.value.trim().toLowerCase();
    applyFilters();
  });

  clearComparison.addEventListener("click", () => {
    selectedIds.clear();
    compareStatus.textContent = "比較候補をすべて解除しました。";
    updateSelectionUi();
  });

  renderProducts();
  renderSourceLedger();
  updateSelectionUi();
})();
