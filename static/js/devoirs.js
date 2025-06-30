document.addEventListener("DOMContentLoaded", function () {
  // Gestion affichage/desactivation du champ tentatives selon checkbox
  const containers = document.querySelectorAll("[data-exercice-container]");

  containers.forEach((container) => {
    const checkbox = container.querySelector("input[name='exercice_id']");
    const tentativesField = container.querySelector(".tentatives-container");

    function toggleTentatives() {
      if (checkbox.checked) {
        tentativesField.style.display = "block";
        tentativesField.querySelector("input").disabled = false;
      } else {
        tentativesField.style.display = "none";
        tentativesField.querySelector("input").disabled = true;
      }
    }

    checkbox.addEventListener("change", toggleTentatives);
    toggleTentatives(); // État initial au chargement
  });

  // Validation du formulaire : au moins un exercice coché
  const form = document.querySelector("form");
  form.addEventListener("submit", function (e) {
    const checkedExercises = document.querySelectorAll(
      "input[name='exercice_id']:checked"
    );
    if (checkedExercises.length === 0) {
      e.preventDefault();
      alert("Veuillez sélectionner au moins un exercice.");
    }
  });
});
