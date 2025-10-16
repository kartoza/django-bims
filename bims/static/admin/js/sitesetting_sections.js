(function () {
  function slugify(text) {
    return text.toLowerCase().trim()
      .replace(/\s+/g, "-").replace(/[^\w-]/g, "");
  }

  function findFieldsets() {
    // Vanilla admin: <fieldset class="module ..."><h2>Title</h2>...</fieldset>
    // Grappelli:     <div class="grp-module grp-collapse">...<h2 class="grp-collapse-handler">Title</h2>...</div>
    var sets = Array.from(document.querySelectorAll("fieldset.module, .grp-module"));
    return sets.map(function (fs) {
      var h2 = fs.querySelector("h2, h2.grp-collapse-handler");
      if (!h2) return null;
      return { el: fs, titleEl: h2, title: h2.textContent || "" };
    }).filter(Boolean);
  }

  function setIds() {
    findFieldsets().forEach(function (s) {
      var id = "section-" + slugify(s.title);
      s.el.id = s.el.id || id;
      // add a 🔗 link button
      if (!s.titleEl.querySelector(".section-anchor")) {
        var a = document.createElement("a");
        a.href = "#" + s.el.id;
        a.className = "section-anchor";
        a.title = "Link to this section";
        a.textContent = " 🔗";
        s.titleEl.appendChild(a);
      }
    });
  }

  function openIfCollapsed(el) {
    // Vanilla admin collapse: fieldset.collapse gets .collapsed and hides .module
    // Grappelli collapse:     .grp-collapse.grp-closed vs grp-open
    if (el.classList.contains("collapsed")) {
      var h2 = el.querySelector("h2");
      if (h2) h2.click();
    }
    if (el.classList.contains("grp-collapse") && el.classList.contains("grp-closed")) {
      // Grappelli toggler is the h2.grp-collapse-handler
      var h2g = el.querySelector("h2.grp-collapse-handler");
      if (h2g) h2g.click();
    }
  }

  function jumpTo(targetId) {
    if (!targetId) return;
    // accept either "gbif" or "section-gbif"
    var el = document.getElementById(targetId) ||
             document.getElementById("section-" + targetId);
    if (!el) return;

    openIfCollapsed(el);
    // scroll and highlight
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    el.style.boxShadow = "0 0 0 3px rgba(0, 150, 250, 0.5) inset";
    setTimeout(function () { el.style.boxShadow = ""; }, 2000);
  }

  document.addEventListener("DOMContentLoaded", function () {
    setIds();

    var hash = (location.hash || "").replace(/^#/, "");
    var params = new URLSearchParams(location.search);
    var section = hash || params.get("section");
    if (section) jumpTo(section);
  });
})();
