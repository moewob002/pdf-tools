// Single source for tool names, routes, colours and icons (used by home, hubs and page headers).
// `category` selects the tool identity colour: convert=blue, edit=violet, ocr=cyan, compress=coral.

export const ICONS = {
  image: "M4 16l4.6-4.6a2 2 0 0 1 2.8 0L16 16m-2-2 1.6-1.6a2 2 0 0 1 2.8 0L20 14m-6-6h.01M6 20h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2z",
  imagesToPdf: "M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.6a1 1 0 0 1 .7.3l5.4 5.4a1 1 0 0 1 .3.7V19a2 2 0 0 1-2 2z",
  word: "M7 21h10a2 2 0 0 0 2-2V9.4a1 1 0 0 0-.3-.7l-5.4-5.4a1 1 0 0 0-.7-.3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2zm1-9 1.5 5 1.5-4 1.5 4L14 12",
  split: "M8 7h12m0 0-4-4m4 4-4 4m0 6H4m0 0 4 4m-4-4 4-4",
  merge: "M12 4v16m8-8H4",
  delete: "M19 7l-.9 12.1A2 2 0 0 1 16.1 21H7.9a2 2 0 0 1-2-1.9L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16",
  ocr: "M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0zM7 10h6M7 7.5h4",
  compress: "M5 8h14M5 8a2 2 0 1 1 0-4h14a2 2 0 1 1 0 4M5 8v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8m-9 4h4",
  convert: "M4 7h11m0 0-3-3m3 3-3 3M20 17H9m0 0 3-3m-3 3 3 3",
  edit: "M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5m-1.4-9.6a2 2 0 1 1 2.8 2.8L11.8 15H9v-2.8l8.6-8.6z",
};

export const CATEGORIES = {
  convert: { title: "Convert", path: "/convert", icon: ICONS.convert, desc: "Turn PDFs into images or Word, and images into PDF." },
  edit: { title: "Edit", path: "/edit", icon: ICONS.edit, desc: "Split, merge and remove pages." },
  ocr: { title: "OCR", path: "/ocr", icon: ICONS.ocr, desc: "Read text from scanned documents." },
  compress: { title: "Compress", path: "/compress", icon: ICONS.compress, desc: "Make PDFs smaller to share." },
};

export const TOOLS = [
  { id: "pdf-to-image", category: "convert", path: "/convert/pdf-to-image", title: "PDF to Images", desc: "Save every page as a PNG, JPG or TIFF image.", tags: ["PNG", "JPG", "TIFF"], icon: ICONS.image },
  { id: "image-to-pdf", category: "convert", path: "/convert/image-to-pdf", title: "Images to PDF", desc: "Combine images into a single PDF.", tags: ["PNG", "JPG", "TIFF", "BMP"], icon: ICONS.imagesToPdf },
  { id: "pdf-to-word", category: "convert", path: "/convert/pdf-to-word", title: "PDF to Word", desc: "Get an editable DOCX document.", tags: ["DOCX"], icon: ICONS.word },
  { id: "split", category: "edit", path: "/edit/split", title: "Split PDF", desc: "Extract chosen pages into separate files.", tags: ["ZIP of pages"], icon: ICONS.split },
  { id: "merge", category: "edit", path: "/edit/merge", title: "Merge PDFs", desc: "Combine PDFs and reorder pages by dragging.", tags: ["Reorder"], icon: ICONS.merge },
  { id: "delete", category: "edit", path: "/edit/delete", title: "Delete Pages", desc: "Remove pages you don't need.", tags: ["Pick pages"], icon: ICONS.delete },
  { id: "ocr", category: "ocr", path: "/ocr", title: "OCR", desc: "Extract text or make scanned PDFs searchable.", tags: ["Text", "Searchable PDF"], icon: ICONS.ocr },
  { id: "compress", category: "compress", path: "/compress", title: "Compress PDF", desc: "Reduce file size with four quality levels.", tags: ["Ghostscript"], icon: ICONS.compress },
];

export const toolById = (id) => TOOLS.find((t) => t.id === id);
export const toolsIn = (category) => TOOLS.filter((t) => t.category === category);
