function getSelectedText() {
  const selection = window.getSelection();
  return selection.toString();
}

function remplacerParSelect(choices) {
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  const select = document.createElement("select");

  choices.forEach((choice) => {
    const option = document.createElement("option");
    option.text = choice;
    select.appendChild(option);
  });

  range.deleteContents();
  range.insertNode(select);
}

function transformerSelectionEnChoix() {
  const texte = getSelectedText();
  if (!texte) {
    alert(
      "Veuillez sélectionner une portion du texte dans la zone de réponse."
    );
    return;
  }

  const saisie = prompt(
    `Entrez les choix possibles pour "${texte}", séparés par des virgules :`
  );
  if (!saisie) return;

  const choix = saisie
    .split(",")
    .map((c) => c.trim())
    .filter(Boolean);
  if (choix.length < 2) {
    alert("Veuillez entrer au moins deux choix.");
    return;
  }

  remplacerParSelect(choix);
}

function prepareContenu() {
  const html = document.getElementById("editableArea").innerHTML;
  document.getElementById("contenu_html").value = html;
  alert("Contenu préparé. Vous pouvez maintenant soumettre le formulaire.");
}
