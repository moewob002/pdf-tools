/**
 * Merge bookkeeping. A "source" is one uploaded file: { id, file, name, status, error }.
 * Files are matched by identity, not by name, so two different "scan.pdf" files both count.
 */

/** Work out which files are new and which sources were removed from the upload list. */
export function diffSources(sources, files) {
  const current = new Set(files);
  const known = new Set(sources.map((s) => s.file));
  return {
    added: files.filter((f) => !known.has(f)),
    removedIds: sources.filter((s) => !current.has(s.file)).map((s) => s.id),
  };
}

/** Drop the pages that belong to removed sources. */
export function withoutSources(pages, removedIds) {
  const removed = new Set(removedIds);
  return pages.filter((p) => !removed.has(p.file_index));
}

/** Build the multipart files list and page_order for /edit/merge-custom. */
export function buildMergeRequest(pages, sources) {
  const byId = new Map(sources.map((s) => [s.id, s]));
  const usedIds = [...new Set(pages.map((p) => p.file_index))].filter((id) => byId.has(id));
  const indexOf = new Map(usedIds.map((id, i) => [id, i]));
  return {
    files: usedIds.map((id) => byId.get(id).file),
    pageOrder: pages
      .filter((p) => indexOf.has(p.file_index))
      .map((p) => ({ file_index: indexOf.get(p.file_index), page: p.page_num })),
  };
}
