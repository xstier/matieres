document.addEventListener("DOMContentLoaded", function () {
  const blankBtn = document.getElementById("insert-blank");
  const choiceBtn = document.getElementById("insert-choices");
  const responseEditor = document.getElementById("reponse_html");

  blankBtn?.addEventListener("click", function (e) {
    e.preventDefault();
    insertAtCursor(responseEditor, `<input type="text" class="blank" />`);
  });

  choiceBtn?.addEventListener("click", function (e) {
    e.preventDefault();
    const userChoices = prompt(
      "Entrez les choix séparés par une virgule (ex: Paris, Londres, Rome)"
    );
    if (userChoices) {
      const choices = userChoices.split(",").map((c) => c.trim());
      const selectHtml = `<select>${choices
        .map((c) => `<option value="${c}">${c}</option>`)
        .join("")}</select>`;
      insertAtCursor(responseEditor, selectHtml);
    }
  });

  function insertAtCursor(input, html) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const text = input.value;
    input.value = text.substring(0, start) + html + text.substring(end);
    input.focus();
    input.selectionStart = input.selectionEnd = start + html.length;
  }
});
