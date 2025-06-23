document.addEventListener("DOMContentLoaded", function () {
  const matiereList = document.getElementById("matiereList");
  const themeList = document.getElementById("themeList");
  const contenuDiv = document.getElementById("contenu");
  const themeTitle = document.getElementById("themeTitle");

  // Lors du clic sur une matière
  matiereList.addEventListener("click", (e) => {
    if (e.target.dataset.id) {
      const matiereId = e.target.dataset.id;
      fetch(`/api/themes/${matiereId}`)
        .then((res) => res.json())
        .then((themes) => {
          themeList.innerHTML = "";
          contenuDiv.innerHTML = "";
          themeTitle.textContent = "";

          if (themes.length === 0) {
            themeList.innerHTML =
              "<li class='list-group-item'>Aucun thème disponible pour cette matière.</li>";
            return;
          }

          themes.forEach((theme) => {
            // Créer l'élément thème
            const liTheme = document.createElement("li");
            liTheme.className = "list-group-item fw-bold";
            liTheme.textContent = theme.nom;

            // Créer la liste des leçons
            const ulLecons = document.createElement("ul");
            ulLecons.classList.add("list-group", "ms-3");

            theme.lecons.forEach((lecon) => {
              const li = document.createElement("li");
              li.className = "list-group-item p-1";

              if (lecon.lien) {
                // Leçon avec fichier : lien direct
                const a = document.createElement("a");
                a.href = lecon.lien;
                a.textContent = lecon.titre;
                a.target = "_blank";
                li.appendChild(a);
              } else {
                // Leçon sans fichier : titre cliquable qui affiche contenu
                const span = document.createElement("span");
                span.textContent = lecon.titre;
                span.style.cursor = "pointer";
                span.classList.add("text-primary");
                span.onclick = () => {
                  contenuDiv.innerHTML = `<h4>${lecon.titre}</h4><p>${
                    lecon.contenu || "Pas de contenu."
                  }</p>`;
                  themeTitle.textContent = theme.nom;
                };
                li.appendChild(span);
              }

              ulLecons.appendChild(li);
            });

            themeList.appendChild(liTheme);
            themeList.appendChild(ulLecons);
          });
        })
        .catch((err) => {
          console.error("Erreur lors du chargement des thèmes :", err);
          themeList.innerHTML =
            "<li class='list-group-item text-danger'>Erreur lors du chargement des thèmes.</li>";
        });
    }
  });
});
