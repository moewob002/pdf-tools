export const THEME_STORAGE_KEY = "pdf-tools-theme";

/** An explicit choice wins; otherwise follow the operating system. */
export function resolveTheme(stored, prefersDark) {
  if (stored === "light" || stored === "dark") return stored;
  return prefersDark ? "dark" : "light";
}

export function readStoredTheme(storage) {
  try {
    return storage?.getItem(THEME_STORAGE_KEY) ?? null;
  } catch {
    return null; // storage can be blocked (private mode, disabled site data)
  }
}

export function storeTheme(storage, theme) {
  try {
    storage?.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // The choice still applies for this visit.
  }
}
