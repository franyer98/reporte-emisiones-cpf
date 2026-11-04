/**
 * Para que el tablero abra sin señal, y abra rápido con ella.
 *
 * Reparto de responsabilidades:
 *
 *   /api/...   SIEMPRE la red primero. Son las cifras. Un dato viejo servido
 *              como bueno engaña, así que la copia sólo entra si no hay señal.
 *
 *   la página  también la red primero. Es código, y servir código viejo como
 *              bueno trae problemas difíciles de ver. La copia entra sólo sin
 *              señal. Abajo está medido por qué no se hace al revés.
 *
 *   lo demás   (librerías, iconos, moldes) la copia, y si no está se baja.
 *              Aquí es donde se gana: son 0,8 MB de librerías que antes venían
 *              dentro del HTML y se bajaban en CADA carga. No cambian salvo que
 *              se cambie el nombre de CACHE, que es lo que hay que hacer al
 *              actualizar una de ellas.
 *
 * Lo que cuelga de /editor no se guarda nunca: es la parte protegida y lo que
 * se escribe ahí tiene que llegar al servidor, no a una copia local.
 */

const CACHE = 'emisiones-v2';

/* Se guardan de entrada para que la segunda visita no espere nada. Las
   librerías son 0,8 MB que antes venían dentro del HTML en cada carga. */
const ESENCIALES = [
  '/', '/manifest.webmanifest',
  '/icono/icono-192.png', '/icono/icono-512.png',
  '/lib/chart.min.js', '/lib/three.min.js', '/lib/orbit.js',
];

self.addEventListener('install', ev => {
  ev.waitUntil(
    caches.open(CACHE)
      // uno por uno: si falla la descarga de alguno, los demás sí quedan
      .then(c => Promise.all(ESENCIALES.map(u => c.add(u).catch(() => {}))))
      .catch(() => {})
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

/* La página: la red primero, la copia como red de seguridad.

   Se probó al revés —servir la copia al instante y refrescar por detrás— y en
   un teléfono de gama baja salía PEOR: sacar 750 KB del almacén de copias pasa
   por el hilo del service worker y, con el procesador justo, cuesta más que
   bajar los 340 KB comprimidos. Medido: 724 ms contra 552 hasta ver algo.
   En un equipo sin apuros sí ganaba, pero no lo bastante para pagar la otra
   mitad del precio: código viejo servido como bueno.
   Lo que de verdad arregló la lentitud fue quitarle peso al documento (2,2 MB
   a 0,75) y sacar las librerías a archivos, que sí se guardan aquí. */
function armazon(ev, pedido) {
  ev.respondWith(
    fetch(pedido)
      .then(r => guardar(pedido, r))
      .catch(() => caches.match(pedido)
        .then(c => c || caches.match('/'))
        .then(c => c || new Response('Sin conexión y sin copia guardada.', {
          status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } }))));
}

self.addEventListener('fetch', ev => {
  const pedido = ev.request;
  if (pedido.method !== 'GET') return;

  const url = new URL(pedido.url);
  if (url.origin !== self.location.origin) return;      // tipografías y demás: que pase derecho
  if (url.pathname.startsWith('/editor/')) return;      // zona protegida: nada de copias

  if (pedido.mode === 'navigate') { armazon(ev, pedido); return; }

  // Las cifras: la red manda.
  if (url.pathname.startsWith('/api/')) {
    ev.respondWith(
      fetch(pedido)
        .then(r => guardar(pedido, r))
        .catch(() => caches.match(pedido)
          .then(c => c || new Response('Sin conexión y sin copia guardada.', {
            status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } }))));
    return;
  }

  // Lo demás: la copia, y si no está se baja.
  ev.respondWith(
    caches.match(pedido).then(c => c || fetch(pedido).then(r => guardar(pedido, r))));
});
