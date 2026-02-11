function getCardData(cardEl) {
  const conceptId = parseInt(cardEl.getAttribute("data-concept-id"), 10);
  const noteInput = cardEl.querySelector(".slot-note");
  const note = noteInput ? noteInput.value : "";
  return { concept_id: conceptId, note };
}

function buildSlotsPayload() {
  const slots = {};
  document.querySelectorAll(".timeframe-slot").forEach(slotEl => {
    const tf = slotEl.getAttribute("data-timeframe");
    const cards = Array.from(slotEl.querySelectorAll(".concept-card"));
    slots[tf] = cards.map(getCardData);
  });
  return { slots };
}

function attachRemoveButtons(container) {
  container.querySelectorAll(".remove-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".concept-card");
      if (card) card.remove();
    });
  });
}

function makeSortableLibrary(libraryEl) {
  // Library: clone items into targets, keep originals.
  Sortable.create(libraryEl, {
    group: { name: "concepts", pull: "clone", put: false },
    sort: false,
    handle: ".drag-handle",
    animation: 150
  });
}

function makeSortableSlot(slotEl) {
  Sortable.create(slotEl, {
    group: { name: "concepts", pull: true, put: true },
    handle: ".drag-handle",
    animation: 150,
    onAdd: function (evt) {
      // When cloned from library, add a remove button if missing
      const card = evt.item;
      if (!card.querySelector(".remove-btn")) {
        const header = card.querySelector(".d-flex.align-items-center.justify-content-between");
        if (header) {
          const removeBtn = document.createElement("button");
          removeBtn.type = "button";
          removeBtn.className = "btn btn-sm btn-outline-danger remove-btn";
          removeBtn.textContent = "Remove";
          header.appendChild(removeBtn);
        }
      }
      attachRemoveButtons(card.parentElement);
    }
  });
}

async function saveSlots() {
  const payload = buildSlotsPayload();

  const resp = await fetch(SAVE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN
    },
    body: JSON.stringify(payload)
  });

  if (!resp.ok) {
    alert("Save failed. Try again.");
    return;
  }

  alert("Saved slots.");
}

document.addEventListener("DOMContentLoaded", () => {
  const libraryEl = document.getElementById("library");
  makeSortableLibrary(libraryEl);

  document.querySelectorAll(".timeframe-slot").forEach(slotEl => makeSortableSlot(slotEl));
  attachRemoveButtons(document);

  const saveBtn = document.getElementById("saveBtn");
  saveBtn.addEventListener("click", saveSlots);
});
