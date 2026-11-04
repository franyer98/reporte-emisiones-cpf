#!/usr/bin/env python3
"""Saca del GOP-F-007 lleno un molde de una sola ficha, en blanco.

El molde conserva el formato tal como lo hizo Ecopetrol —rótulos, combinados,
bordes, el logo y la configuración de impresión— y pierde los datos, las fotos
de los trece cierres viejos, los comentarios y las hojas sobrantes. Pesa unos
60 KB en vez de 2,9 MB, que es lo que permite que el tablero lo descargue y lo
rellene en el teléfono.

No se usa openpyxl: al reescribir pierde el logo y los combinados. Se trabaja
sobre el zip, pieza por pieza, como con el GOP-F-006.
"""

import re
import shutil
import zipfile

ORIGEN = '/home/claude/cierres/GOP-F-007.xlsx'
DESTINO = '/home/claude/cierres/GOP-F-007-molde.xlsx'
HOJA_MODELO = 'MODELO'

# Las casillas que el tablero rellena. Se vacían dejando el estilo, que es lo
# que da el borde y el fondo de la casilla.
CASILLAS = ['D5', 'K5', 'D6', 'K6', 'D7', 'K7', 'D8', 'K8', 'D9', 'K9',
            'D10', 'K10', 'E12', 'B24', 'K23', 'K24', 'K25']

# Lo que se conserva del archivo original.
GUARDAR = {
    '[Content_Types].xml', '_rels/.rels',
    'docProps/app.xml', 'docProps/core.xml',
    'xl/workbook.xml', 'xl/_rels/workbook.xml.rels',
    'xl/styles.xml', 'xl/theme/theme1.xml', 'xl/sharedStrings.xml',
    'xl/worksheets/sheet1.xml', 'xl/worksheets/_rels/sheet1.xml.rels',
    'xl/drawings/drawing1.xml', 'xl/drawings/_rels/drawing1.xml.rels',
    'xl/media/image1.png',
    'xl/printerSettings/printerSettings1.bin',
}


def _vaciar_celdas(hoja: str) -> str:
    """Deja la casilla con su estilo pero sin contenido."""
    for ref in CASILLAS:
        hoja = re.sub(
            r'<c r="%s"([^>]*?)(?:/>|>.*?</c>)' % ref,
            lambda m: '<c r="%s"%s/>' % (ref, re.sub(r'\s*t="\w+"', '', m.group(1))),
            hoja, count=1, flags=re.S)
    return hoja


def _solo_logo(dibujo: str) -> str:
    """Quita del dibujo todo lo que no sea el logo (la única ancla de arriba)."""
    anclas = re.findall(r'<xdr:twoCellAnchor.*?</xdr:twoCellAnchor>', dibujo, re.S)
    conservadas = [a for a in anclas
                   if re.search(r'<xdr:row>([0-9]+)</xdr:row>', a)
                   and int(re.search(r'<xdr:row>([0-9]+)</xdr:row>', a).group(1)) < 5]
    cuerpo = ''.join(conservadas)
    cab = dibujo[:dibujo.index('<xdr:twoCellAnchor')]
    return cab + cuerpo + '</xdr:wsDr>'


def _rels_sin_sobras(rels: str, dejar: tuple) -> str:
    """Deja sólo las relaciones indicadas, conservando la etiqueta raíz.

    Ojo con cortar por «<Relationship»: también casa con «<Relationships», que
    es el contenedor, y el archivo sale sin raíz y no lo abre nadie. Hay que
    cortar después de esa etiqueta de apertura.
    """
    apertura = re.search(r'<Relationships[^>]*>', rels)
    if not apertura:
        raise ValueError('estas relaciones no tienen etiqueta raíz')
    salida = [m.group(0) for m in re.finditer(r'<Relationship\s[^>]*/>', rels)
              if any(p in m.group(0) for p in dejar)]
    return rels[:apertura.end()] + ''.join(salida) + '</Relationships>'


def construir() -> str:
    z = zipfile.ZipFile(ORIGEN)
    piezas = {n: z.read(n) for n in z.namelist() if n in GUARDAR}

    # ---- la hoja: sin datos, sin comentarios
    hoja = piezas['xl/worksheets/sheet1.xml'].decode('utf-8')
    hoja = _vaciar_celdas(hoja)
    hoja = re.sub(r'<legacyDrawing[^>]*/>', '', hoja)
    piezas['xl/worksheets/sheet1.xml'] = hoja.encode('utf-8')

    # ---- sus enlaces: sólo impresión y dibujo
    piezas['xl/worksheets/_rels/sheet1.xml.rels'] = _rels_sin_sobras(
        piezas['xl/worksheets/_rels/sheet1.xml.rels'].decode('utf-8'),
        ('printerSettings', 'drawings/drawing1.xml')).encode('utf-8')

    # ---- el dibujo: sólo el logo
    piezas['xl/drawings/drawing1.xml'] = _solo_logo(
        piezas['xl/drawings/drawing1.xml'].decode('utf-8')).encode('utf-8')
    piezas['xl/drawings/_rels/drawing1.xml.rels'] = _rels_sin_sobras(
        piezas['xl/drawings/_rels/drawing1.xml.rels'].decode('utf-8'),
        ('media/image1.png',)).encode('utf-8')

    # ---- el libro: una sola hoja, con nombre de molde
    wb = piezas['xl/workbook.xml'].decode('utf-8')
    primera = re.search(r'<sheet[^>]*?r:id="rId1"[^>]*/>', wb)
    if not primera:
        primera = re.search(r'<sheet[^>]*/>', wb)
    hoja_xml = re.sub(r'name="[^"]*"', 'name="%s"' % HOJA_MODELO, primera.group(0))
    hoja_xml = re.sub(r'sheetId="\d+"', 'sheetId="1"', hoja_xml)
    wb = re.sub(r'<sheets>.*?</sheets>', '<sheets>%s</sheets>' % hoja_xml, wb, flags=re.S)
    wb = re.sub(r'<definedNames>.*?</definedNames>', '', wb, flags=re.S)
    # El libro venía abriendo en la hoja 13 (activeTab="12"). Con una sola hoja
    # —o con tres— esa pestaña no existe, y Excel se niega a abrir el archivo
    # diciendo que encontró un problema con el contenido. LibreOffice lo ignora,
    # así que el error no se ve hasta que alguien lo abre en Excel de verdad.
    wb = re.sub(r'firstSheet="\d+"', 'firstSheet="0"', wb)
    wb = re.sub(r'activeTab="\d+"', 'activeTab="0"', wb)
    piezas['xl/workbook.xml'] = wb.encode('utf-8')

    piezas['xl/_rels/workbook.xml.rels'] = _rels_sin_sobras(
        piezas['xl/_rels/workbook.xml.rels'].decode('utf-8'),
        ('worksheets/sheet1.xml', 'styles.xml', 'theme/theme1.xml',
         'sharedStrings.xml')).encode('utf-8')

    # ---- el índice de piezas: fuera todo lo que ya no está
    ct = piezas['[Content_Types].xml'].decode('utf-8')
    conservar = []
    for m in re.finditer(r'<(Default|Override)[^>]*/>', ct):
        t = m.group(0)
        if t.startswith('<Default'):
            conservar.append(t)
            continue
        parte = re.search(r'PartName="([^"]+)"', t).group(1).lstrip('/')
        if parte in piezas:
            conservar.append(t)
    cab = ct[:ct.index('<Default')]
    piezas['[Content_Types].xml'] = (cab + ''.join(conservar)
                                     + '</Types>').encode('utf-8')

    # ---- las relaciones del paquete: fuera customXml y docMetadata
    piezas['_rels/.rels'] = _rels_sin_sobras(
        piezas['_rels/.rels'].decode('utf-8'),
        ('xl/workbook.xml', 'docProps/core.xml', 'docProps/app.xml')).encode('utf-8')

    # app.xml heredaba la lista de las catorce hojas viejas y de sus rangos
    # con nombre; Excel compara esa lista con el libro y avisa si no cuadra.
    import fichas
    piezas['docProps/app.xml'] = fichas.app_xml([HOJA_MODELO])

    with zipfile.ZipFile(DESTINO, 'w', zipfile.ZIP_DEFLATED) as out:
        for nombre in ['[Content_Types].xml', '_rels/.rels'] + \
                      [n for n in piezas if n not in ('[Content_Types].xml', '_rels/.rels')]:
            out.writestr(nombre, piezas[nombre])
    z.close()
    return DESTINO


if __name__ == '__main__':
    ruta = construir()
    import os
    print(f'  molde: {ruta}')
    print(f'  pesa {os.path.getsize(ruta) / 1024:.0f} KB '
          f'(el original, {os.path.getsize(ORIGEN) / 1048576:.1f} MB)')
