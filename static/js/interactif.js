document.addEventListener("DOMContentLoaded", () => {
  const blankBtn = document.getElementById("insert-blank");
  const choiceBtn = document.getElementById("insert-choices");
  const responseEditor = document.getElementById("reponse_html");

  // Insère un champ texte à la position du curseur dans la textarea/input
  function insertAtCursor(input, html) {
    if (!input) return;

    const start = input.selectionStart;
    const end = input.selectionEnd;
    const text = input.value;

    // Insère le html à la position du curseur
    input.value = text.slice(0, start) + html + text.slice(end);

    // Replace le curseur juste après le contenu inséré
    input.focus();
    input.selectionStart = input.selectionEnd = start + html.length;
  }

  blankBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    insertAtCursor(responseEditor, `<input type="text" class="blank" />`);
  });

  choiceBtn?.addEventListener("click", (e) => {
    e.preventDefault();

    const userChoices = prompt(
      "Entrez les choix séparés par une virgule (ex: Paris, Londres, Rome)"
    );

    if (!userChoices) return;

    // Nettoyage des choix : trim + filtre des vides
    const choices = userChoices
      .split(",")
      .map((c) => c.trim())
      .filter((c) => c.length > 0);

    if (choices.length === 0) return;

    // Crée la chaîne HTML du select avec options
    const selectHtml = `<select>${choices
      .map((c) => `<option value="${c}">${c}</option>`)
      .join("")}</select>`;

    insertAtCursor(responseEditor, selectHtml);
  });
});
