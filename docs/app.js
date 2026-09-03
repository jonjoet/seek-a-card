(function () {
  "use strict";

  const cards = Array.isArray(window.SEEK_A_CARD_CARDS)
    ? window.SEEK_A_CARD_CARDS.filter(isValidCard)
    : [];
  const categories = [...new Set(cards.map((card) => card.category))];
  const categoryIcons = Object.freeze({
    "Animals": "🐾",
    "Food": "🍎",
    "Things": "🧸",
    "On the go": "🚲",
    "Nature": "🌻",
    "Shapes & colors": "◆"
  });
  const storageKey = "seek-a-card:settings:v1";
  const views = [...document.querySelectorAll(".view")];
  const state = loadState();

  let currentCard = null;
  let questionCount = 0;
  let roundWasGuessed = false;
  let activeView = "start-view";

  const elements = {
    homeButton: document.getElementById("home-button"),
    settingsButton: document.getElementById("settings-button"),
    infoButton: document.getElementById("info-button"),
    categoryControls: document.getElementById("category-controls"),
    difficultyControls: document.getElementById("difficulty-controls"),
    deckSummary: document.getElementById("deck-summary"),
    startButton: document.getElementById("start-button"),
    readyButton: document.getElementById("ready-button"),
    secretImage: document.getElementById("secret-image"),
    secretTitle: document.getElementById("secret-title"),
    secretCategory: document.getElementById("secret-category"),
    hideButton: document.getElementById("hide-button"),
    skipButton: document.getElementById("skip-button"),
    questionCount: document.getElementById("question-count"),
    counterMessage: document.getElementById("counter-message"),
    minusButton: document.getElementById("minus-button"),
    plusButton: document.getElementById("plus-button"),
    guessedButton: document.getElementById("guessed-button"),
    revealButton: document.getElementById("reveal-button"),
    resultKicker: document.getElementById("result-kicker"),
    resultImage: document.getElementById("result-image"),
    resultTitle: document.getElementById("result-title"),
    resultDetail: document.getElementById("result-detail"),
    nextButton: document.getElementById("next-button"),
    changeDeckButton: document.getElementById("change-deck-button"),
    settingsDialog: document.getElementById("settings-dialog"),
    infoDialog: document.getElementById("info-dialog"),
    cardSearch: document.getElementById("card-search"),
    cardSettingsList: document.getElementById("card-settings-list"),
    settingsSummary: document.getElementById("settings-summary"),
    showAllButton: document.getElementById("show-all-button"),
    clearHistoryButton: document.getElementById("clear-history-button")
  };

  function isValidCard(card) {
    return Boolean(
      card &&
      typeof card.id === "string" && /^[a-z0-9-]+$/.test(card.id) &&
      typeof card.label === "string" && card.label.length <= 40 &&
      typeof card.category === "string" && card.category.length <= 40 &&
      (card.difficulty === "easy" || card.difficulty === "tricky") &&
      typeof card.image === "string" && /^assets\/cards\/[A-F0-9-]+\.svg$/.test(card.image)
    );
  }

  function defaultState() {
    return {
      selectedCategories: [...categories],
      difficulty: "easy",
      disabledIds: [],
      recentIds: []
    };
  }

  function loadState() {
    const defaults = defaultState();
    try {
      const parsed = JSON.parse(localStorage.getItem(storageKey));
      if (!parsed || typeof parsed !== "object") return defaults;
      const knownIds = new Set(cards.map((card) => card.id));
      const selectedCategories = Array.isArray(parsed.selectedCategories)
        ? parsed.selectedCategories.filter((category) => categories.includes(category))
        : defaults.selectedCategories;
      return {
        selectedCategories: selectedCategories.length ? selectedCategories : defaults.selectedCategories,
        difficulty: parsed.difficulty === "all" ? "all" : "easy",
        disabledIds: Array.isArray(parsed.disabledIds)
          ? [...new Set(parsed.disabledIds.filter((id) => knownIds.has(id)))].slice(0, cards.length)
          : [],
        recentIds: Array.isArray(parsed.recentIds)
          ? [...new Set(parsed.recentIds.filter((id) => knownIds.has(id)))].slice(0, 120)
          : []
      };
    } catch (_error) {
      return defaults;
    }
  }

  function saveState() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (_error) {
      // The game remains usable when storage is blocked or full.
    }
  }

  function showView(id) {
    activeView = id;
    views.forEach((view) => {
      view.hidden = view.id !== id;
    });
    elements.homeButton.hidden = id === "start-view";
    window.scrollTo({ top: 0, behavior: "instant" });
    const heading = document.querySelector(`#${id} h1`);
    if (heading) {
      heading.setAttribute("tabindex", "-1");
      heading.focus({ preventScroll: true });
    }
  }

  function createCategoryControls() {
    const fragment = document.createDocumentFragment();
    categories.forEach((category) => {
      const button = document.createElement("button");
      button.className = "category-button";
      button.type = "button";
      button.dataset.category = category;
      button.setAttribute("aria-pressed", String(state.selectedCategories.includes(category)));

      const icon = document.createElement("span");
      icon.className = "category-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = categoryIcons[category] || "•";

      const label = document.createElement("span");
      label.textContent = category;
      button.append(icon, label);
      button.addEventListener("click", () => toggleCategory(category));
      fragment.append(button);
    });
    elements.categoryControls.replaceChildren(fragment);
  }

  function toggleCategory(category) {
    const selected = new Set(state.selectedCategories);
    if (selected.has(category)) {
      if (selected.size === 1) return;
      selected.delete(category);
    } else {
      selected.add(category);
    }
    state.selectedCategories = categories.filter((item) => selected.has(item));
    saveState();
    updateSetupControls();
  }

  function updateSetupControls() {
    document.querySelectorAll("[data-category]").forEach((button) => {
      button.setAttribute("aria-pressed", String(state.selectedCategories.includes(button.dataset.category)));
    });
    document.querySelectorAll("[data-difficulty]").forEach((button) => {
      button.setAttribute("aria-pressed", String(state.difficulty === button.dataset.difficulty));
    });
    const pool = getEligibleCards();
    const categoryCount = state.selectedCategories.length;
    elements.deckSummary.textContent = `${pool.length} cards from ${categoryCount} ${categoryCount === 1 ? "category" : "categories"}`;
    elements.startButton.disabled = pool.length === 0;
    elements.startButton.textContent = pool.length ? "Start a round" : "No cards available";
  }

  function getEligibleCards() {
    const disabled = new Set(state.disabledIds);
    return cards.filter((card) =>
      state.selectedCategories.includes(card.category) &&
      !disabled.has(card.id) &&
      (state.difficulty === "all" || card.difficulty === "easy")
    );
  }

  function randomIndex(length) {
    if (!Number.isSafeInteger(length) || length < 1) return 0;
    if (window.crypto && typeof window.crypto.getRandomValues === "function") {
      const ceiling = Math.floor(0x100000000 / length) * length;
      const numbers = new Uint32Array(1);
      do {
        window.crypto.getRandomValues(numbers);
      } while (numbers[0] >= ceiling);
      return numbers[0] % length;
    }
    return Math.floor(Math.random() * length);
  }

  function chooseCard() {
    const pool = getEligibleCards();
    if (!pool.length) {
      showView("start-view");
      updateSetupControls();
      return null;
    }
    const recent = new Set(state.recentIds);
    let choices = pool.filter((card) => !recent.has(card.id));
    if (!choices.length) {
      state.recentIds = [];
      choices = pool;
    }
    const card = choices[randomIndex(choices.length)];
    state.recentIds = [card.id, ...state.recentIds.filter((id) => id !== card.id)]
      .slice(0, Math.min(120, Math.max(1, pool.length - 1)));
    saveState();
    return card;
  }

  function prepareSecretCard() {
    currentCard = chooseCard();
    if (!currentCard) return;
    questionCount = 0;
    roundWasGuessed = false;
    elements.secretImage.src = currentCard.image;
    elements.secretImage.alt = `Illustration of ${currentCard.label}`;
    elements.secretTitle.textContent = currentCard.label;
    elements.secretCategory.textContent = `${currentCard.category} · ${currentCard.difficulty === "easy" ? "Familiar" : "Trickier"}`;
    showView("secret-view");
  }

  function beginRound() {
    currentCard = null;
    questionCount = 0;
    showView("pass-view");
  }

  function updateCounter() {
    elements.questionCount.textContent = String(questionCount);
    elements.minusButton.disabled = questionCount === 0;
    elements.plusButton.disabled = questionCount === 20;
    if (questionCount === 20) {
      elements.counterMessage.textContent = "That’s twenty—time for a final guess!";
    } else if (questionCount >= 15) {
      elements.counterMessage.textContent = `${20 - questionCount} questions left.`;
    } else if (questionCount === 0) {
      elements.counterMessage.textContent = "Tap after each question.";
    } else {
      elements.counterMessage.textContent = `${20 - questionCount} questions left.`;
    }
  }

  function revealResult(guessed) {
    if (!currentCard) return;
    roundWasGuessed = Boolean(guessed);
    elements.resultImage.src = currentCard.image;
    elements.resultImage.alt = `Illustration of ${currentCard.label}`;
    elements.resultTitle.textContent = currentCard.label;
    elements.resultKicker.textContent = roundWasGuessed ? "Nice guessing! It was" : "The answer was";
    const questionText = `${questionCount} ${questionCount === 1 ? "question" : "questions"}`;
    elements.resultDetail.textContent = `${currentCard.category} · ${questionText}`;
    showView("result-view");
  }

  function openSettings() {
    elements.cardSearch.value = "";
    renderCardSettings("");
    elements.settingsDialog.showModal();
    elements.cardSearch.focus();
  }

  function renderCardSettings(query) {
    const normalized = query.trim().toLocaleLowerCase().slice(0, 40);
    const disabled = new Set(state.disabledIds);
    const matches = cards.filter((card) =>
      !normalized || card.label.toLocaleLowerCase().includes(normalized) || card.category.toLocaleLowerCase().includes(normalized)
    );
    const fragment = document.createDocumentFragment();

    matches.forEach((card) => {
      const label = document.createElement("label");
      label.className = "card-setting";

      const image = document.createElement("img");
      image.src = card.image;
      image.alt = "";
      image.width = 40;
      image.height = 40;

      const text = document.createElement("span");
      text.className = "card-setting-text";
      const name = document.createElement("strong");
      name.textContent = card.label;
      const detail = document.createElement("span");
      detail.textContent = card.category;
      text.append(name, detail);

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !disabled.has(card.id);
      checkbox.setAttribute("aria-label", `Include ${card.label}`);
      checkbox.addEventListener("change", () => setCardEnabled(card.id, checkbox.checked));

      label.append(image, text, checkbox);
      fragment.append(label);
    });

    if (!matches.length) {
      const empty = document.createElement("p");
      empty.className = "empty-search";
      empty.textContent = "No cards match that search.";
      fragment.append(empty);
    }

    elements.cardSettingsList.replaceChildren(fragment);
    const visibleCount = cards.length - disabled.size;
    elements.settingsSummary.textContent = `${visibleCount} of ${cards.length} cards are available`;
  }

  function setCardEnabled(cardId, enabled) {
    const disabled = new Set(state.disabledIds);
    if (enabled) disabled.delete(cardId);
    else disabled.add(cardId);
    state.disabledIds = cards.map((card) => card.id).filter((id) => disabled.has(id));
    saveState();
    renderCardSettings(elements.cardSearch.value);
    updateSetupControls();
  }

  function closeDialog(dialogId) {
    const dialog = document.getElementById(dialogId);
    if (dialog && dialog.open) dialog.close();
  }

  function registerEvents() {
    elements.difficultyControls.addEventListener("click", (event) => {
      const button = event.target.closest("[data-difficulty]");
      if (!button) return;
      state.difficulty = button.dataset.difficulty === "all" ? "all" : "easy";
      saveState();
      updateSetupControls();
    });
    elements.startButton.addEventListener("click", beginRound);
    elements.readyButton.addEventListener("click", prepareSecretCard);
    elements.hideButton.addEventListener("click", () => {
      updateCounter();
      showView("play-view");
    });
    elements.skipButton.addEventListener("click", prepareSecretCard);
    elements.plusButton.addEventListener("click", () => {
      questionCount = Math.min(20, questionCount + 1);
      updateCounter();
    });
    elements.minusButton.addEventListener("click", () => {
      questionCount = Math.max(0, questionCount - 1);
      updateCounter();
    });
    elements.guessedButton.addEventListener("click", () => revealResult(true));
    elements.revealButton.addEventListener("click", () => revealResult(false));
    elements.nextButton.addEventListener("click", beginRound);
    elements.changeDeckButton.addEventListener("click", () => showView("start-view"));
    elements.homeButton.addEventListener("click", () => showView("start-view"));
    elements.settingsButton.addEventListener("click", openSettings);
    elements.infoButton.addEventListener("click", () => elements.infoDialog.showModal());
    elements.cardSearch.addEventListener("input", () => renderCardSettings(elements.cardSearch.value));
    elements.showAllButton.addEventListener("click", () => {
      state.disabledIds = [];
      saveState();
      renderCardSettings(elements.cardSearch.value);
      updateSetupControls();
    });
    elements.clearHistoryButton.addEventListener("click", () => {
      state.recentIds = [];
      saveState();
      elements.clearHistoryButton.textContent = "Recent cards cleared";
      window.setTimeout(() => {
        elements.clearHistoryButton.textContent = "Clear recent cards";
      }, 1600);
    });
    document.querySelectorAll("[data-close-dialog]").forEach((button) => {
      button.addEventListener("click", () => closeDialog(button.dataset.closeDialog));
    });
    [elements.settingsDialog, elements.infoDialog].forEach((dialog) => {
      dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
      });
    });
    window.addEventListener("popstate", () => {
      if (activeView !== "start-view") showView("start-view");
    });
  }

  function registerServiceWorker() {
    if ("serviceWorker" in navigator && window.isSecureContext) {
      navigator.serviceWorker.register("service-worker.js", { scope: "./" }).catch(() => {
        // Online play still works if private browsing blocks service workers.
      });
    }
  }

  createCategoryControls();
  updateSetupControls();
  registerEvents();
  registerServiceWorker();
})();
