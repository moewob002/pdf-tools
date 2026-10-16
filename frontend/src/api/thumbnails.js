import api from "./index";
import { retryOnRateLimit } from "../utils/retry";

/** Page thumbnails for a PDF: [{ page, image (base64 JPEG) }]. */
export async function loadThumbnails(file, dpi = 100) {
  const form = new FormData();
  form.append("file", file);
  form.append("dpi", String(dpi));
  const res = await retryOnRateLimit(() => api.post("/edit/thumbnails", form));
  return res.data.pages;
}
