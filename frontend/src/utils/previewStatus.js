/** Status chip for a single uploaded PDF whose page previews are being read. */
export function previewStatus({ loading, failed, pageCount }) {
  if (loading) return { state: "loading", label: "Reading…" };
  if (failed) return { state: "error", label: "Can't read" };
  if (pageCount > 0) return { state: "ready", label: `${pageCount} page${pageCount !== 1 ? "s" : ""}` };
  return { state: "ready", label: "Ready" };
}
