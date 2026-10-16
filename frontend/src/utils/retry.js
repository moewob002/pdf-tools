/**
 * Call `fn`, retrying while it fails with HTTP 429 (the backend rate-limits bursts,
 * e.g. when many PDFs are added to a merge at once).
 */
export async function retryOnRateLimit(fn, { delays = [2000, 4000, 6000], sleep = defaultSleep } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error?.response?.status !== 429 || attempt >= delays.length) throw error;
      await sleep(delays[attempt]);
    }
  }
}

function defaultSleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
