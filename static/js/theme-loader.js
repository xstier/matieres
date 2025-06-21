document.addEventListener("DOMContentLoaded", () => {
  const matiereSelect = document.getElementById("matiere-select");
  const themeSelect = document.getElementById("theme-select");

  matiereSelect.addEventListener("change", () => {
    const matiereId = matiereSelect.value;

    fetch(`/api/themes/${matiereId}`)
      .then((response) => response.json())
      .then((themes) => {
        themeSelect.innerHTML = "";
        themes.forEach((theme) => {
          const option = document.createElement("option");
          option.value = theme._id;
          option.textContent = theme.nom;
          themeSelect.appendChild(option);
        });
      });
  });

  // Déclenche au chargement initial
  matiereSelect.dispatchEvent(new Event("change"));
});
