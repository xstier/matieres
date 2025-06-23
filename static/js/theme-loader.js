document.addEventListener("DOMContentLoaded", function () {
  const matiereSelect = document.getElementById("matiere-select");
  const themeSelect = document.getElementById("theme-select");

  if (matiereSelect) {
    matiereSelect.addEventListener("change", function () {
      const matiereId = this.value;
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
        })
        .catch(() => {
          themeSelect.innerHTML =
            '<option value="">Erreur de chargement</option>';
        });
    });
  }
});
