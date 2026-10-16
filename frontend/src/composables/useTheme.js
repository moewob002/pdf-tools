import { ref } from "vue";
import { readStoredTheme, resolveTheme, storeTheme } from "../utils/theme";

const media = typeof window !== "undefined" && window.matchMedia
  ? window.matchMedia("(prefers-color-scheme: dark)")
  : null;

// index.html has already applied the theme before first paint; start from it.
const theme = ref(document.documentElement.getAttribute("data-theme") || "light");

function apply(value) {
  theme.value = value;
  document.documentElement.setAttribute("data-theme", value);
}

// Follow OS changes until the user makes an explicit choice.
media?.addEventListener("change", (e) => {
  if (!readStoredTheme(window.localStorage)) apply(resolveTheme(null, e.matches));
});

export function useTheme() {
  function toggle() {
    const next = theme.value === "dark" ? "light" : "dark";
    storeTheme(window.localStorage, next);
    apply(next);
  }
  return { theme, toggle };
}
