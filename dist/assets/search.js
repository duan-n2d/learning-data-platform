(function () {
  const root = window.__ROOT_PREFIX__ || "";
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);

  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
    });
  }

  const input = document.getElementById("searchInput");
  const results = document.getElementById("searchResults");
  let index = [];

  fetch(root + "search-index.json")
    .then((r) => r.json())
    .then((data) => { index = data; })
    .catch(() => {});

  function normalize(s) { return (s || "").toLowerCase(); }

  if (input && results) {
    input.addEventListener("input", () => {
      const q = normalize(input.value.trim());
      if (q.length < 2) {
        results.style.display = "none";
        results.innerHTML = "";
        return;
      }
      const words = q.split(/\s+/).filter(Boolean);
      const matches = index
        .map((item) => {
          const hay = normalize(item.title + " " + item.description + " " + item.text);
          const score = words.reduce((acc, w) => acc + (hay.includes(w) ? 1 : 0), 0);
          return { item, score };
        })
        .filter((x) => x.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 8);

      results.innerHTML = matches.map(({ item }) => `
        <a class="search-result" href="${root}${item.url}">
          <strong>${item.title}</strong>
          <small>${item.description || item.section || "Lesson"}</small>
        </a>
      `).join("");
      results.style.display = matches.length ? "block" : "none";
    });

    document.addEventListener("click", (e) => {
      if (!results.contains(e.target) && e.target !== input) results.style.display = "none";
    });
  }
})();
