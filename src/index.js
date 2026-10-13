/**
 * Guarda los datos del tablero en el servidor.
 *
 *   GET  /api/datos               lectura pública: es lo que el tablero muestra.
 *   POST /editor/api/datos        guardar.
 *   GET  /editor/api/versiones    lista de copias de los últimos siete días.
 *   POST /editor/api/restaurar    vuelve a una de esas copias.
 *
 * Todo lo que cuelga de /editor está protegido por Cloudflare Access: nadie
 * llega ahí sin haber pasado por el código que se envía al correo.
 * Lo demás se sirve tal cual desde los archivos publicados.
 */

const CLAVE = 'datos';
const PREFIJO = 'v:';
const SIETE_DIAS = 7 * 24 * 60 * 60;   // en segundos, que es lo que espera KV

function esValido(d) {
  return d && ['DATA1', 'DATA2', 'CERRADAS1', 'CERRADAS2'].every(k => Array.isArray(d[k]));
}

const texto = (t, status = 200) =>
  new Response(t, { status, headers: { 'content-type': 'text/plain; charset=utf-8' } });

const json = (t, status = 200) =>
  new Response(t, { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

/* Access pone esta cabecera al dejar pasar a quien se identificó. Si falta,
   la petición no vino por la puerta. */
const autorizado = request => !!request.headers.get('cf-access-jwt-assertion');

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const ruta = url.pathname;

    if (ruta === '/api/datos' && request.method === 'GET') {
      const guardado = await env.EMISIONES.get(CLAVE);
      // sin nada guardado todavía: el tablero usa los datos que trae dentro
      return guardado ? json(guardado) : texto('sin datos guardados', 404);
    }

    if (ruta === '/editor/api/datos') {
      if (request.method !== 'POST') return texto('método no permitido', 405);
      if (!autorizado(request)) return texto('sin autorización', 403);

      const cuerpo = await request.text();
      let datos;
      try { datos = JSON.parse(cuerpo); } catch (e) { datos = null; }
      if (!esValido(datos)) return texto('datos con formato inesperado', 400);

      // La copia se guarda con su fecha y se borra sola a los siete días.
      const sello = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      await env.EMISIONES.put(PREFIJO + sello, cuerpo, { expirationTtl: SIETE_DIAS });
      await env.EMISIONES.put(CLAVE, cuerpo);
      return texto('guardado');
    }

    if (ruta === '/editor/api/versiones' && request.method === 'GET') {
      if (!autorizado(request)) return texto('sin autorización', 403);
      const { keys } = await env.EMISIONES.list({ prefix: PREFIJO });
      // de la más reciente a la más antigua
      const lista = keys
        .map(k => ({ clave: k.name, fecha: k.name.slice(PREFIJO.length) }))
        .sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
      return json(JSON.stringify(lista));
    }

    if (ruta === '/editor/api/restaurar' && request.method === 'POST') {
      if (!autorizado(request)) return texto('sin autorización', 403);
      const { clave } = await request.json().catch(() => ({}));
      if (!clave || !clave.startsWith(PREFIJO)) return texto('copia no indicada', 400);

      const copia = await env.EMISIONES.get(clave);
      if (!copia) return texto('esa copia ya no existe', 404);

      // lo que hay ahora también se archiva: restaurar tiene vuelta atrás
      const actual = await env.EMISIONES.get(CLAVE);
      if (actual) {
        const sello = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
        await env.EMISIONES.put(PREFIJO + sello, actual, { expirationTtl: SIETE_DIAS });
      }
      await env.EMISIONES.put(CLAVE, copia);
      return texto('restaurado');
    }

    return env.ASSETS.fetch(request);
  },
};
