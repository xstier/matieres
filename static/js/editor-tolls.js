document.addEventListener("DOMContentLoaded", () => {
  const editor = document.getElementById("editor");
  const output = document.getElementById("reponse_html");

  document.querySelector("form").addEventListener("submit", () => {
    output.value = editor.innerHTML;
  });

  document.getElementById("add-blank").addEventListener("click", () => {
    const input = document.createElement("input");
    input.setAttribute("type", "text");
    input.setAttribute("class", "blank");
    input.setAttribute("placeholder", "Réponse attendue");

    insertAtCursor(input);
  });

  document.getElementById("add-choices").addEventListener("click", () => {
    const selectedText = window.getSelection().toString();
    const choices = prompt(
      `Choix possibles pour "${selectedText}" (séparés par des virgules) :`
    );

    if (choices) {
      const select = document.createElement("select");
      choices.split(",").forEach((c) => {
        const option = document.createElement("option");
        option.textContent = c.trim();
        select.appendChild(option);
      });
      insertAtCursor(select);
    }
  });

  function insertAtCursor(element) {
    const sel = window.getSelection();
    if (sel.rangeCount === 0) return;

    const range = sel.getRangeAt(0);
    range.deleteContents();
    range.insertNode(element);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
  }
});
