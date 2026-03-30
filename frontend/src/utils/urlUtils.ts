/**
 * URL utility helpers shared across the frontend.
 */

/**
 * Returns true when the URL hostname matches the Three HK UAT environment
 * (`wwwuat.three.com.hk`). Used to decide whether to show the
 * "🔐 UAT credentials auto-applied" badge in RunTestButton without showing
 * a browser profile picker.
 */
export function isUatUrl(url: string): boolean {
  if (!url) return false;
  try {
    const { hostname } = new URL(url);
    return hostname === 'wwwuat.three.com.hk';
  } catch {
    return false;
  }
}
