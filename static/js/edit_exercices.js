document.addEventListener("DOMContentLoaded", function () {
  const previewZone = document.getElementById("preview_zone");
  const hiddenField = document.getElementById("reponse_html");

  // Avant la soumission du formulaire, nettoyer le HTML
  const form = document.querySelector("form");
  form.addEventListener("submit", function () {
    // Cloner pour ne pas modifier l'affichage
    const clone = previewZone.cloneNode(true);

    // Supprimer tous les boutons <button> et leur contenu
    const buttons = clone.querySelectorAll("button");
    buttons.forEach((btn) => btn.remove());

    // Supprimer aussi les espaces vides résiduels s'il y en a
    hiddenField.value = clone.innerHTML.trim();
  });

  // Ajouter les boutons "Modifier" aux <select> existants
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

// ========== MISE À JOUR DES <SELECT> EXISTANTS ==========

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

// ========== MODIFICATION DES OPTIONS DU <SELECT> ==========

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

    // Vider les anciennes options
    select.innerHTML = "";

    newOptions.forEach((opt) => {
      const optionEl = document.createElement("option");
      optionEl.value = opt;
      optionEl.textContent = opt;
      select.appendChild(optionEl);
    });
  }
}
