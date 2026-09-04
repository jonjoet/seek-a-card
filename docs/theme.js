/* Applies the saved appearance before first paint.
   This runs synchronously in <head>, ahead of app.js, so a device set to dark
   does not flash a dark frame at someone who chose the light theme. It reads
   the same stored settings object the app writes, and nothing else. */
(function () {
  "use strict";

  try {
    const raw = localStorage.getItem("seek-a-card:settings:v1");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    const theme = parsed && parsed.theme;
    if (theme === "light" || theme === "dark") {
      document.documentElement.setAttribute("data-theme", theme);
    }
  } catch (_error) {
    // Blocked or unparsable storage simply leaves the device preference in place.
  }
})();
