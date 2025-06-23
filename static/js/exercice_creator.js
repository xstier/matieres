document.addEventListener("DOMContentLoaded", function () {
  const matiereSelect = document.getElementById("matiere-select");
  const themeSelect = document.getElementById("theme-select");
  const editor = document.getElementById("editor");
  const hiddenInput = document.getElementById("reponse_html");
  const addBlankBtn = document.getElementById("add-blank");
  const addChoicesBtn = document.getElementById("add-choices");
  const importFileBtn = document.getElementById("import-file-btn");
  const fileInput = document.getElementById("file-upload");
  const form = document.querySelector("form");

  let fieldCounter = 0;
  function getUniqueFieldName() {
    return `field_${fieldCounter++}`;
  }

  function loadThemes(matiereId) {
    themeSelect.innerHTML = '<option value="">Chargement...</option>';
    if (!matiereId) {
      themeSelect.innerHTML =
        '<option value="">-- Choisir un thème --</option>';
      return;
    }

    fetch(`/api/themes/${matiereId}`)
      .then((res) => res.json())
      .then((themes) => {
        themeSelect.innerHTML =
          '<option value="">-- Choisir un thème --</option>';
        themes.forEach((theme) => {
          const option = document.createElement("option");
          option.value = theme._id;
          option.textContent = theme.nom;
          themeSelect.appendChild(option);
        });
        themeSelect.selectedIndex = 0;
      })
      .catch((err) => {
        console.error("Erreur chargement des thèmes :", err);
        themeSelect.innerHTML =
          '<option value="">Erreur de chargement</option>';
      });
  }

  if (matiereSelect) {
    matiereSelect.addEventListener("change", () => {
      const matiereId = matiereSelect.value;
      loadThemes(matiereId);
    });
  }

  function insertNodeAtCursor(node) {
    editor.focus();
    const sel = window.getSelection();
    if (sel.getRangeAt && sel.rangeCount) {
      let range = sel.getRangeAt(0);
      if (!editor.contains(range.commonAncestorContainer)) {
        range = document.createRange();
        range.selectNodeContents(editor);
        range.collapse(false);
        sel.removeAllRanges();
        sel.addRange(range);
      }
      range.deleteContents();
      range.insertNode(node);
      range.setStartAfter(node);
      range.collapse(true);
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      editor.appendChild(node);
    }
    editor.focus();
  }

  function adjustSelectWidth(select) {
    const tempSpan = document.createElement("span");
    tempSpan.style.visibility = "hidden";
    tempSpan.style.whiteSpace = "nowrap";
    tempSpan.style.position = "absolute";
    document.body.appendChild(tempSpan);

    let maxWidth = 0;
    for (const option of select.options) {
      tempSpan.textContent = option.textContent;
      maxWidth = Math.max(maxWidth, tempSpan.offsetWidth);
    }

    document.body.removeChild(tempSpan);
    select.style.width = `${maxWidth + 30}px`;
  }

  if (addBlankBtn) {
    addBlankBtn.addEventListener("click", () => {
      const input = document.createElement("input");
      input.type = "text";
      input.className = "interactive-blank";
      input.style.width = "80px";
      input.placeholder = "…";
      input.name = getUniqueFieldName();
      input.addEventListener("input", () => {
        input.setAttribute("value", input.value);
      });

      insertNodeAtCursor(input);
      insertNodeAtCursor(document.createTextNode(" "));
    });
  }

  if (addChoicesBtn) {
    addChoicesBtn.addEventListener("click", () => {
      const choices = prompt("Entrez les choix séparés par des virgules :");
      if (choices) {
        const options = choices.split(",").map((opt) => opt.trim());
        const select = document.createElement("select");
        select.className = "interactive-select";
        select.name = getUniqueFieldName();

        const firstOption = document.createElement("option");
        firstOption.value = "";
        firstOption.disabled = true;
        firstOption.selected = true;
        firstOption.textContent = "- sélectionnez la bonne réponse -";
        select.appendChild(firstOption);

        options.forEach((opt) => {
          const option = document.createElement("option");
          option.value = opt;
          option.textContent = opt;
          select.appendChild(option);
        });

        select.addEventListener("change", () => {
          for (const option of select.options)
            option.removeAttribute("selected");
          select.options[select.selectedIndex].setAttribute("selected", true);
        });

        adjustSelectWidth(select);
        insertNodeAtCursor(select);
        insertNodeAtCursor(document.createTextNode(" "));
      }
    });
  }

  function extractReponsesAttendues(editor) {
    const reponses = {};
    const inputs = editor.querySelectorAll(
      "input.interactive-blank, select.interactive-select"
    );
    inputs.forEach((el) => {
      const name = el.getAttribute("name");
      if (!name) return;
      const value = el.value || "";
      reponses[name] = value;

      el.setAttribute("value", value);
      if (el.tagName.toLowerCase() === "select") {
        Array.from(el.options).forEach((opt) =>
          opt.removeAttribute("selected")
        );
        if (el.selectedIndex >= 0) {
          el.options[el.selectedIndex].setAttribute("selected", "selected");
        }
      }
    });
    return reponses;
  }

  function removeHiddenElements(node) {
    for (let i = node.children.length - 1; i >= 0; i--) {
      const child = node.children[i];
      const style = window.getComputedStyle(child);
      if (
        style.display === "none" ||
        style.visibility === "hidden" ||
        child.hidden
      ) {
        child.remove();
      } else {
        removeHiddenElements(child);
      }
    }
  }

  function syncEditorFieldsBeforeSubmit() {
    editor.querySelectorAll("input.interactive-blank").forEach((input) => {
      input.setAttribute("value", input.value);
    });

    editor.querySelectorAll("select.interactive-select").forEach((select) => {
      for (const option of select.options) option.removeAttribute("selected");
      const selected = select.options[select.selectedIndex];
      if (selected) selected.setAttribute("selected", true);
    });
  }

  if (form && hiddenInput && editor) {
    form.addEventListener("submit", (e) => {
      syncEditorFieldsBeforeSubmit();

      const clone = editor.cloneNode(true);
      removeHiddenElements(clone);
      hiddenInput.value = clone.innerHTML;

      let hiddenReponses = form.querySelector(
        'input[name="reponses_attendues"]'
      );
      if (!hiddenReponses) {
        hiddenReponses = document.createElement("input");
        hiddenReponses.type = "hidden";
        hiddenReponses.name = "reponses_attendues";
        form.appendChild(hiddenReponses);
      }
      hiddenReponses.value = JSON.stringify(extractReponsesAttendues(editor));
    });
  }

  function insertTextAtCursor(text) {
    const textNode = document.createTextNode(text);
    insertNodeAtCursor(textNode);
  }

  function updateHiddenInput() {
    hiddenInput.value = editor.innerHTML;
  }

  if (importFileBtn && fileInput) {
    importFileBtn.addEventListener("click", () => {
      const file = fileInput.files[0];
      if (!file) {
        alert("Choisis un fichier Word ou PDF d'abord !");
        return;
      }

      const reader = new FileReader();
      reader.onload = function (event) {
        const arrayBuffer = event.target.result;

        if (
          file.type ===
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) {
          mammoth
            .extractRawText({ arrayBuffer })
            .then((result) => {
              insertTextAtCursor(result.value);
              updateHiddenInput();
            })
            .catch((err) => alert("Erreur lecture Word : " + err));
        } else if (file.type === "application/pdf") {
          const typedarray = new Uint8Array(arrayBuffer);
          pdfjsLib.getDocument(typedarray).promise.then((pdf) => {
            let promises = [];
            for (let j = 1; j <= pdf.numPages; j++) {
              promises.push(
                pdf
                  .getPage(j)
                  .then((page) =>
                    page
                      .getTextContent()
                      .then((textContent) =>
                        textContent.items.map((item) => item.str).join(" ")
                      )
                  )
              );
            }
            Promise.all(promises).then((pagesText) => {
              insertTextAtCursor(pagesText.join("\n\n"));
              updateHiddenInput();
            });
          });
        } else {
          alert("Format non supporté. Utilise un fichier .docx ou .pdf");
        }
      };
      reader.readAsArrayBuffer(file);
    });
  }
});
