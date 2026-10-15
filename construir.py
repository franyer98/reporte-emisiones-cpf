"""
Genera las dos caras del tablero a partir de un solo archivo fuente.

    index.html         tablero público: ver, filtrar, mapas, informe. Sin edición.
    editor/index.html  el mismo tablero, con edición, cierres y clave.

La idea es que la página que ve cualquiera no lleve dentro una sola línea
capaz de cambiar datos, en vez de llevarla y taparla con un candado. Lo que
no existe no se puede forzar.

El editor queda bajo /editor para que Cloudflare Access proteja esa ruta y
deje el tablero abierto.
"""

import os
import re
import shutil

FUENTE = 'trabajo.html'
REPO = 'repo'

# Bloque completo del módulo de edición, delimitado por su comentario de cabecera
INICIO_EDICION = '/* ============================================================\n   EDICIÓN DIRECTA'
FIN_EDICION = "})();\n\n(function () {\n  const ed = document.getElementById('navEditar');"

# Enganches sueltos que viven fuera del módulo
RECORTES = [
    # el enganche del menú al modo edición
    ('''(function () {
  const ed = document.getElementById('navEditar');
  if (ed) ed.addEventListener('click', e => {
    e.preventDefault();
    const m = document.querySelector('.nav-menu');
    if (m) m.classList.remove('open');
    if (window.modoEdicion) window.modoEdicion(true);
  });
})();

''', ''),
    # botón "Registrar un cierre" de la pestaña Cierres
    ('      <button class="bd-b bd-pri ci-nuevo" id="ciNuevo">Registrar un cierre</button>\n\n', ''),
    # marcas de edición en tarjetas, filas y cierres
    ('    if (window.MODO_EDICION && editable(data)) marcarEditable(card, d, data);\n', ''),
    ('  if (window.MODO_EDICION && editable(data)) el.appendChild(tarjetaAgregar(data));\n', ''),
    ('      if (window.MODO_EDICION) marcarEditable(card, d, g.lista);\n', ''),
    ('  if (window.MODO_EDICION && grupos.length) grid.appendChild(tarjetaAgregar(grupos[0].lista));\n', ''),
    ('    if (window.MODO_EDICION && item && editable(data)) marcarEditable(row, item, data);\n', ''),
]

# Funciones auxiliares de edición que quedan colgando al quitar el módulo
FUNCIONES = ['function editable(lista) {', 'function marcarEditable(card, d, lista) {',
             'function tarjetaAgregar(lista) {']


def bloque(texto, inicio):
    """Devuelve el rango de una función que empieza en `inicio`, contando llaves."""
    i = texto.index(inicio)
    j = texto.index('{', i)
    nivel = 0
    for k in range(j, len(texto)):
        if texto[k] == '{':
            nivel += 1
        elif texto[k] == '}':
            nivel -= 1
            if nivel == 0:
                return i, k + 1
    raise ValueError('sin cierre: ' + inicio[:40])


def publica(src):
    """El tablero sin nada que permita cambiar datos."""
    i = src.index(INICIO_EDICION)
    j = src.index(FIN_EDICION) + len('})();\n')
    out = src[:i] + src[j:]

    for viejo, nuevo in RECORTES:
        if viejo not in out:
            raise ValueError('no se halló el recorte: ' + viejo.strip()[:60])
        out = out.replace(viejo, nuevo)

    for f in FUNCIONES:
        a, b = bloque(out, f)
        out = out[:a] + out[b:]

    # El acceso al modo edición no tiene sentido donde no hay edición
    out = out.replace(
        '<a href="#" class="nav-editar" id="navEditar"><span>Activar modo edición</span>'
        '<small>Agregar, corregir y cerrar hallazgos</small></a>\n', '')

    # El acceso al editor va como botón, no como un renglón más entre quince:
    # puesto en la lista pasaba desapercibido incluso para quien lo buscaba.
    out = out.replace(
        '<div class="nav-group-title">DATOS</div>',
        '<div class="nav-group-title">DATOS</div>\n'
        '        <a href="editor/" class="nav-editar">'
        '<span>Editar datos</span><small>Pide tu correo y un código</small></a>')
    return out


def comprobar(out):
    """Nada de lo que escribe datos puede sobrevivir en la versión pública."""
    prohibido = ['modoEdicion', 'abrirFormulario', 'abrirSelectorCierre', 'PIN_HASH',
                 'marcarEditable', 'tarjetaAgregar', 'registrarLlave', 'descargarTablero',
                 'id="ciNuevo"', 'id="bdEditar"', 'MODO_EDICION']
    hallados = [p for p in prohibido if p in out]
    if hallados:
        raise SystemExit('quedó código de edición en la pública: ' + ', '.join(hallados))


def main():
    src = open(FUENTE, encoding='utf8').read()

    pub = publica(src)
    comprobar(pub)

    os.makedirs(os.path.join(REPO, 'editor'), exist_ok=True)
    open(os.path.join(REPO, 'index.html'), 'w', encoding='utf8').write(pub)
    shutil.copyfile(FUENTE, os.path.join(REPO, 'editor', 'index.html'))

    kb = lambda t: round(len(t.encode()) / 1024)
    print(f'index.html        {kb(pub):>5} KB   sin edición')
    print(f'editor/index.html {kb(src):>5} KB   completo')
    print(f'diferencia        {kb(src) - kb(pub):>5} KB de código de edición retirado')


if __name__ == '__main__':
    main()
