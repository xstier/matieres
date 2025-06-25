document.addEventListener("DOMContentLoaded", function () {
  const previewZone = document.getElementById("preview_zone");
  const hiddenField = document.getElementById("reponse_html");

  // Synchroniser le contenu avant soumission
  const form = document.querySelector("form");
  form.addEventListener("submit", function () {
    // Clone pour ne pas modifier l'affichage
    const clone = previewZone.cloneNode(true);

    // Supprimer tous les boutons "Modifier"
    const buttons = clone.querySelectorAll("button");
    buttons.forEach((btn) => {
      if (btn.textContent.includes("Modifier")) {
        btn.remove();
      }
    });

    // Nettoyer les attributs inutiles si besoin ici

    // Transférer dans le champ caché
    hiddenField.value = clone.innerHTML.trim();
  });

  // Ajouter boutons Modifier aux selects existants
  enhanceSelects(previewZone);
});

// ========== AJOUTS D'ÉLÉMENTS ==========

function addInput() {
  const div = document.createElement("div");
  div.innerHTML = `
    <label>Champ texte :
      <input type="text" name="input_${Date.now()}" placeholder="Réponse" class="form-control my-2" />
    </label>
  `;
  document.getElementById("preview_zone").appendChild(div);
}

function addTextarea() {
  const div = document.createElement("div");
  div.innerHTML = `
    <label>Zone texte :
      <textarea name="textarea_${Date.now()}" class="form-control my-2" rows="3"></textarea>
    </label>
  `;
  document.getElementById("preview_zone").appendChild(div);
}

function addSelect() {
  const div = document.createElement("div");
  const timestamp = Date.now();
  div.innerHTML = `
    <label>Menu déroulant :
      <select name="select_${timestamp}" class="form-select my-2">
        <option value="Option 1">Option 1</option>
        <option value="Option 2">Option 2</option>
      </select>
      <button type="button" class="btn btn-sm btn-warning ms-2" onclick="editSelectOptions(this)">Modifier</button>
    </label>
  `;
  document.getElementById("preview_zone").appendChild(div);
}

// ========== AJOUT DES BOUTONS MODIFIER ==========

function enhanceSelects(container) {
  const selects = container.querySelectorAll("select");

  selects.forEach((select) => {
    const next = select.nextElementSibling;
    const alreadyHasButton =
      next &&
      next.tagName === "BUTTON" &&
      next.textContent.includes("Modifier");

    if (!alreadyHasButton) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-sm btn-warning ms-2";
      btn.textContent = "Modifier";
      btn.onclick = () => editSelectOptions(btn);
      select.parentNode.insertBefore(btn, select.nextSibling);
    }
  });
}

// ========== MODIFICATION DYNAMIQUE DES OPTIONS ==========

function editSelectOptions(button) {
  const select = button.previousElementSibling;

  if (!select || select.tagName.toLowerCase() !== "select") return;

  const currentOptions = Array.from(select.options)
    .map((opt) => opt.value)
    .join(", ");
  const userInput = prompt(
    "Modifier les options (séparées par des virgules) :",
    currentOptions
  );

  if (userInput !== null) {
    const newOptions = userInput
      .split(",")
      .map((opt) => opt.trim())
      .filter((opt) => opt !== "");

    select.innerHTML = "";
    newOptions.forEach((opt) => {
      const optionEl = document.createElement("option");
      optionEl.value = opt;
      optionEl.textContent = opt;
      select.appendChild(optionEl);
    });
  }
}
