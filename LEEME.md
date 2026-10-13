# Tablero de emisiones fugitivas · CPF-1, CPF-2 y Caño Sur

## Qué es cada archivo

    trabajo.html        El original. Todo cambio se hace AQUÍ.
    construir.py        Genera las dos caras a partir de trabajo.html.
    index.html          Tablero público. Generado: no editarlo a mano.
    editor/index.html   El mismo tablero con edición. Generado.
    src/index.js        Programa que guarda los datos en Cloudflare.
    wrangler.jsonc      Configuración de la publicación.

`index.html` y `editor/index.html` se sobrescriben cada vez que se construye,
así que cualquier cambio hecho directamente sobre ellos se pierde.

## Para cambiar algo

    python3 construir.py
    git add -A && git commit -m "lo que cambió" && git push

Cloudflare publica solo al recibir el push.

`construir.py` quita de la versión pública todo el código capaz de escribir
datos, y se niega a terminar si queda algún resto. La idea es que la página
que ve cualquiera no lleve dentro una sola línea con la que cambiar nada:
lo que no existe no se puede forzar.

## Dónde están los datos

En el almacén KV de Cloudflare, no en este repositorio. El tablero los pide a
`/api/datos` al abrir; el editor los envía a `/editor/api/datos` al pulsar
Guardar, ruta protegida por Cloudflare Access.

Los datos que trae `trabajo.html` dentro son una copia de respaldo: es lo que
se ve mientras llega la respuesta del servidor, y lo único que queda si se
abre el archivo sin conexión. Se va quedando atrás a medida que se edita.

## Cada guardado deja copia

Se conservan las de los últimos siete días; después se borran solas. El botón
*Historial*, en la barra de edición, las lista y permite volver a cualquiera.
