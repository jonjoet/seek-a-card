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
async function warmArtwork(cache) {
  const pending = [];
  for (const href of artworkUrls) {
    if (!(await cache.match(href))) pending.push(href);
  }
  const batchSize = 12;
  for (let index = 0; index < pending.length; index += batchSize) {
    await Promise.all(
      pending.slice(index, index + batchSize).map((href) => cache.add(href).catch(() => {
        // One unreachable illustration must not fail the whole installation.
      }))
    );
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(appShell);
    await warmArtwork(cache);
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

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response.ok || response.type === "opaque") return response;
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        return response;
      });
    }).catch(() => caches.match(new URL("./index.html", scopeUrl).href))
  );
});
