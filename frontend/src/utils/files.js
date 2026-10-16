/** Does `file` match an <input accept> string such as ".pdf" or "image/*"? */
export function matchesAccept(file, accept) {
  if (!accept) return true;
  const name = (file.name || "").toLowerCase();
  const type = (file.type || "").toLowerCase();
  return accept
    .split(",")
    .map((rule) => rule.trim().toLowerCase())
    .filter(Boolean)
    .some((rule) => {
      if (rule.startsWith(".")) return name.endsWith(rule);
      if (rule.endsWith("/*")) return type.startsWith(rule.slice(0, -1));
      return type === rule;
    });
}

/** Split candidate files into accepted ones and rejected ones with a reason. */
export function partitionFiles(files, { accept = "", maxBytes = Infinity, typeLabel = "file type" } = {}) {
  const accepted = [];
  const rejected = [];
  for (const file of files) {
    if (!matchesAccept(file, accept)) {
      rejected.push({ file, reason: `Not a supported ${typeLabel}` });
    } else if (file.size > maxBytes) {
      rejected.push({ file, reason: `Larger than ${Math.round(maxBytes / (1024 * 1024))}MB` });
    } else if (file.size === 0) {
      rejected.push({ file, reason: "File is empty" });
    } else {
      accepted.push(file);
    }
  }
  return { accepted, rejected };
}
