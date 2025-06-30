function preloadReponsesAttendues(reponsesAttendues) {
  const previewZone = document.getElementById("preview_zone");
  if (!previewZone) return;

  Object.entries(reponsesAttendues).forEach(([name, value]) => {
    const fields = previewZone.querySelectorAll(`[name="${name}"]`);
    fields.forEach((field) => {
      if (!field) return;
      const tag = field.tagName.toLowerCase();
      if (tag === "select") {
        [...field.options].forEach((opt) => {
          opt.selected = opt.value === value;
        });
      } else if (tag === "input") {
        const type = field.getAttribute("type");
        if (type === "checkbox") {
          if (Array.isArray(value)) {
            field.checked = value.includes(field.value);
          } else {
            field.checked = field.value === value;
          }
        } else {
          field.value = value;
        }
      } else if (tag === "textarea") {
        field.value = value;
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const previewZone = document.getElementById("preview_zone");
  const hiddenField = document.getElementById("reponse_html");
  const form = document.querySelector("form");

  // Initialiser fieldCounter à partir des fields existants (ex: field_0, field_1, ...)
  let fieldCounter = 0;
  if (previewZone) {
    const inputs = previewZone.querySelectorAll("[name^='field_']");
    if (inputs.length > 0) {
      const maxIndex = Array.from(inputs).reduce((max, el) => {
        const n = parseInt(el.name.replace("field_", ""), 10);
        return n > max ? n : max;
      }, 0);
      fieldCounter = maxIndex + 1;
    }
  }

  // Préremplir les réponses attendues si l'objet est injecté par le serveur
  if (window.REPONSES_ATTENDUES) {
    preloadReponsesAttendues(window.REPONSES_ATTENDUES);
  }

  // Avant la soumission, nettoyer et mettre à jour le champ caché
  form.addEventListener("submit", () => {
    const clone = previewZone.cloneNode(true);
    clone.querySelectorAll("button").forEach((btn) => btn.remove());
    hiddenField.value = clone.innerHTML.trim();
  });

  // Ajouter boutons modifier aux selects existants
  enhanceSelects(previewZone);

  // Ajout dynamique de champs
  window.addInput = function () {
    const div = document.createElement("div");
    const name = `field_${fieldCounter++}`;
    div.innerHTML = `
      <label>Champ texte :
        <input type="text" name="${name}" placeholder="Réponse" class="form-control my-2" />
      </label>
    `;
    previewZone.appendChild(div);
  };

  window.addTextarea = function () {
    const div = document.createElement("div");
    const name = `field_${fieldCounter++}`;
    div.innerHTML = `
      <label>Zone texte :
        <textarea name="${name}" class="form-control my-2" rows="3"></textarea>
      </label>
    `;
    previewZone.appendChild(div);
  };

  window.addSelect = function () {
    const div = document.createElement("div");
    const name = `field_${fieldCounter++}`;
    div.innerHTML = `
      <label>Menu déroulant :
        <select name="${name}" class="form-select my-2">
          <option value="Option 1">Option 1</option>
          <option value="Option 2">Option 2</option>
        </select>
        <button type="button" class="btn btn-sm btn-warning ms-2">Modifier</button>
      </label>
    `;
    previewZone.appendChild(div);
    const btn = div.querySelector("button");
    btn.onclick = () => editSelectOptions(btn);
  };

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

  window.editSelectOptions = function (button) {
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
  };
});
