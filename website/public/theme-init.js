// Theme: follows prefers-color-scheme by default. Only an explicit click on the toggle is remembered
// (localStorage "obc-theme", per browser, never sent anywhere). External synchronous file: runs before first
// paint and stays CSP-safe (no inline script).
(function () {
  var root = document.documentElement;
  var KEY = "obc-theme";
  try {
    var t = localStorage.getItem(KEY);
    if (t === "light" || t === "dark") root.setAttribute("data-theme", t);
  } catch (e) {}
  root.classList.add("js");
  function current() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  function label(btn) {
    btn.setAttribute("aria-label", current() === "light" ? "Switch to dark theme" : "Switch to light theme");
  }
  document.addEventListener("DOMContentLoaded", function () {
    var btns = document.querySelectorAll("[data-theme-toggle]");
    for (var i = 0; i < btns.length; i++) {
      label(btns[i]);
      btns[i].addEventListener("click", function (ev) {
        var next = current() === "light" ? "dark" : "light";
        root.setAttribute("data-theme", next);
        try { localStorage.setItem(KEY, next); } catch (e) {}
        label(ev.currentTarget);
        document.dispatchEvent(new CustomEvent("obc:theme"));
      });
    }
  });
})();
