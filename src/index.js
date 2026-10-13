/**
 * Guarda los datos del tablero en el servidor.
 *
 *   GET  /api/datos          lectura pública: es lo que el tablero muestra.
 *   POST /editor/api/datos   escritura. Cuelga de /editor a propósito: esa ruta
 *                            ya está protegida por Cloudflare Access, así que
 *                            nadie llega aquí sin haber pasado por el código
 *                            que se envía al correo.
 *
 * Todo lo demás se sirve tal cual desde los archivos publicados.
 */

const CLAVE = 'datos';

function esValido(d) {
  return d && ['DATA1', 'DATA2', 'CERRADAS1', 'CERRADAS2'].every(k => Array.isArray(d[k]));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/datos' && request.method === 'GET') {
      const guardado = await env.EMISIONES.get(CLAVE);
      if (!guardado) {
        // sin nada guardado todavía: el tablero usa los datos que trae dentro
        return new Response('sin datos guardados', { status: 404 });
      }
      return new Response(guardado, {
        headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
      });
    }

    if (url.pathname === '/editor/api/datos') {
      if (request.method !== 'POST') return new Response('método no permitido', { status: 405 });
      // Access pone esta cabecera al dejar pasar a quien se identificó
      if (!request.headers.get('cf-access-jwt-assertion')) {
        return new Response('sin autorización', { status: 403 });
      }
      const texto = await request.text();
      let datos;
      try { datos = JSON.parse(texto); } catch (e) { datos = null; }
      if (!esValido(datos)) return new Response('datos con formato inesperado', { status: 400 });

      // copia anterior, por si hay que volver atrás
      const previo = await env.EMISIONES.get(CLAVE);
      if (previo) await env.EMISIONES.put(CLAVE + '-anterior', previo);

      await env.EMISIONES.put(CLAVE, texto);
      return new Response('guardado', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
    }

    return env.ASSETS.fetch(request);
  },
};
