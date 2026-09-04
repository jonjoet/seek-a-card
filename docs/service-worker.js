"use strict";

importScripts("asset-list.js");

const CACHE_NAME = self.SEEK_A_CARD_CACHE_NAME;
const scopeUrl = new URL(self.registration.scope);
const safeUrls = new Set(
  self.SEEK_A_CARD_SAFE_ASSETS.map((path) => new URL(path, scopeUrl).href)
);
const appShell = [
  "./",
  "./index.html",
  "./styles.css",
  "./cards.js",
  "./app.js",
  "./manifest.webmanifest",
  "./icon.svg",
  "./maskable-icon.svg",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
].map((path) => new URL(path, scopeUrl).href);

const shellSet = new Set(appShell);
const artworkUrls = [...safeUrls].filter((href) => !shellSet.has(href));

// Card artwork is precached during install, while the previous worker keeps
// serving the page. Without this, a deck taken offline before every card had
// been shown would render the unseen ones as broken images.
//
// Installation is all or nothing. Activation deletes the previous cache, so a
// worker that activated with a partial precache would replace a complete
// offline deck with an incomplete one and leave the missing cards broken. A
// batch of transient network errors must therefore fail the install: the
// existing worker stays active, keeps its complete cache, and a later update
// attempt tries again. Anything already stored is kept, so that retry resumes
// rather than refetching the whole deck.
async function addWithRetry(cache, href) {
  for (let attempt = 0; ; attempt += 1) {
    try {
      await cache.add(href);
      return;
    } catch (error) {
      if (attempt >= 2) throw error;
      await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
    }
  }
}

async function warmArtwork(cache) {
  const pending = [];
  for (const href of artworkUrls) {
    if (!(await cache.match(href))) pending.push(href);
  }
  const batchSize = 12;
  for (let index = 0; index < pending.length; index += batchSize) {
    await Promise.all(pending.slice(index, index + batchSize).map((href) => addWithRetry(cache, href)));
  }
}

// Storage pressure can evict an entry between writing it and activating, so the
// allowlist is checked once more before this worker is allowed to take over.
async function verifyPrecache(cache) {
  const missing = [];
  for (const href of safeUrls) {
    if (!(await cache.match(href))) missing.push(href);
  }
  if (missing.length) {
    throw new Error(`Incomplete precache: ${missing.length} of ${safeUrls.size} assets are missing`);
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(appShell);
    await warmArtwork(cache);
    await verifyPrecache(cache);
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== scopeUrl.origin || !safeUrls.has(url.href)) {
    event.respondWith(new Response("Blocked by the local asset allowlist.", {
      status: 403,
      headers: { "Content-Type": "text/plain; charset=utf-8" }
    }));
    return;
  }

  // Reads are scoped to this worker's own cache. A failed installation leaves a
  // partly filled cache behind so the next attempt can resume, and the global
  // caches.match() would happily serve a half-written generation from it.
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (!response.ok || response.type === "opaque") return response;
          cache.put(request, response.clone());
          return response;
        });
      }).catch(() => cache.match(new URL("./index.html", scopeUrl).href))
    )
  );
});
