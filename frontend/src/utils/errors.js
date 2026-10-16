/**
 * Turn an axios error into a message for the user.
 *
 * File downloads use `responseType: "blob"`, so error bodies arrive as a Blob and
 * `error.response.data.detail` is undefined; the JSON has to be read out of the Blob.
 */
export async function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const response = error?.response;
  if (!response) {
    if (error?.code === "ECONNABORTED") return "The request timed out. Try a smaller file.";
    return "Could not reach the server. Check your connection and try again.";
  }

  let data = response.data;
  if (typeof Blob !== "undefined" && data instanceof Blob) {
    try {
      data = JSON.parse(await data.text());
    } catch {
      data = null;
    }
  }
  const detail = data && typeof data === "object" ? data.detail : null;
  if (typeof detail === "string" && detail) return detail;

  if (response.status === 413) return "The upload is too large.";
  if (response.status === 429) return "Too many requests. Please wait a moment and try again.";
  return fallback;
}
