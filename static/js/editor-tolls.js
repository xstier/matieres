document.addEventListener("DOMContentLoaded", () => {
  const editor = document.getElementById("editor");
  const output = document.getElementById("reponse_html");
  const form = document.querySelector("form");
  const addBlankBtn = document.getElementById("add-blank");
  const addChoicesBtn = document.getElementById("add-choices");

  // Lors de la soumission du formulaire, on récupère le contenu HTML de l'éditeur dans le champ caché
  form.addEventListener("submit", () => {
    output.value = editor.innerHTML;
  });

  // Ajoute un champ texte (blanc) à l'emplacement du curseur dans l'éditeur
  addBlankBtn.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "blank";
    input.placeholder = "Réponse attendue";
    insertAtCursor(input);
    editor.focus();
  });

  // Ajoute une liste déroulante (select) avec des choix issus d'une saisie utilisateur, autour du texte sélectionné
  addChoicesBtn.addEventListener("click", () => {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (!selectedText) {
      alert("Veuillez sélectionner un texte avant d'ajouter des choix.");
      return;
    }

    const choices = prompt(
      `Choix possibles pour "${selectedText}" (séparés par des virgules) :`
    );
    if (!choices) return;

    const select = document.createElement("select");
    choices.split(",").forEach((choice) => {
      const option = document.createElement("option");
      option.textContent = choice.trim();
      select.appendChild(option);
    });

    insertAtCursor(select);
    editor.focus();
  });

  // Fonction utilitaire pour insérer un élément DOM à la position actuelle du curseur dans l'éditeur
  function insertAtCursor(element) {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;

    const range = sel.getRangeAt(0);
    range.deleteContents();

    // Pour insérer correctement, on clone l'élément si plusieurs insertions peuvent avoir lieu
    const node = element.cloneNode(true);
    range.insertNode(node);

    // Positionner le curseur après l'élément inséré
    range.setStartAfter(node);
    range.collapse(true);

    sel.removeAllRanges();
    sel.addRange(range);
  }
});
