export function track(name, detail = {}) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: `museum_${name}`, ...detail, timestamp: Date.now() });
}
