/**
 * Para que el tablero abra sin señal.
 *
 * En campo no siempre hay datos, así que se guarda una copia de la página y
 * de la última lectura del servidor. La regla general es "primero la red":
 * si hay señal se ve lo último publicado, y sólo si no la hay se tira de la
 * copia. Así nadie se queda mirando una versión vieja sin saberlo.
 *
 * Lo que cuelga de /editor no se guarda nunca: es la parte protegida y lo que
 * se escribe ahí tiene que llegar al servidor, no a una copia local.
 */

const CACHE = 'emisiones-v1';
const ESENCIALES = ['/', '/manifest.webmanifest', '/icono/icono-192.png', '/icono/icono-512.png'];

self.addEventListener('install', ev => {
  ev.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ESENCIALES))
      .catch(() => {})            // sin red al instalar: se guarda luego, al navegar
      .then(() => self.skipWaiting()));
});

self.addEventListener('activate', ev => {
  ev.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

function guardar(pedido, respuesta) {
  if (respuesta && respuesta.ok) {
    const copia = respuesta.clone();
    caches.open(CACHE).then(c => c.put(pedido, copia)).catch(() => {});
  }
  return respuesta;
}

self.addEventListener('fetch', ev => {
  const pedido = ev.request;
  if (pedido.method !== 'GET') return;

  const url = new URL(pedido.url);
  if (url.origin !== self.location.origin) return;      // tipografías y demás: que pase derecho
  if (url.pathname.startsWith('/editor/')) return;      // zona protegida: nada de copias

  // La página y todo lo que venga de /api: primero la red, la copia sólo como
  // red de seguridad. Nunca al revés: un dato viejo servido como bueno engaña.
  const esPagina = pedido.mode === 'navigate';
  const esDatos = url.pathname.startsWith('/api/');

  if (esPagina || esDatos) {
    ev.respondWith(
      fetch(pedido)
        .then(r => guardar(pedido, r))
        .catch(() => caches.match(pedido)
          .then(c => c || (esPagina ? caches.match('/') : undefined))
          .then(c => c || new Response('Sin conexión y sin copia guardada.', {
            status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } }))));
    return;
  }

  // Lo demás (iconos, librerías) no cambia: vale la copia, y si no está se baja.
  ev.respondWith(
    caches.match(pedido).then(c => c || fetch(pedido).then(r => guardar(pedido, r))));
});
