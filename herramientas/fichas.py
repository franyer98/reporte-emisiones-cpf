#!/usr/bin/env python3
"""Arma un GOP-F-007 con una ficha por cierre, a partir del molde.

Esta es la misma cirugía que hará el tablero en el teléfono; se escribe primero
aquí porque en Python se puede comprobar el resultado abriéndolo de verdad, y
porque pasarlo después a JavaScript es traducción, no diseño.

Por cada cierre se clona la hoja MODELO y se le escriben diecisiete casillas.
Las fotos se incrustan como piezas del archivo, ancladas donde el formato tiene
los dos marcos. Lo que ninguna máquina puede saber —las firmas, las actividades
ejecutadas, la fecha de verificación— se deja en blanco a propósito.
"""

from __future__ import annotations

import datetime
import re
import zipfile

MOLDE = '/home/claude/cierres/GOP-F-007-molde.xlsx'

# Las dos anclas de foto, copiadas del formato original: el marco izquierdo
# (condición inicial) y el derecho (condición final).
ANCLA_INICIAL = (1, 44450, 14, 25400, 6, 584200, 20, 374650)
ANCLA_FINAL = (8, 31750, 14, 12700, 13, 679450, 20, 368300)


def serie(iso: str) -> int | None:
    """Fecha ISO a número de serie de Excel."""
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(iso or ''))
    if not m:
        return None
    d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (d - datetime.date(1899, 12, 30)).days


def _esc(t) -> str:
    return (str('' if t is None else t).replace('&', '&amp;')
            .replace('<', '&lt;').replace('>', '&gt;'))


def _escribir(hoja: str, ref: str, valor, numero: bool = False) -> str:
    """Mete un valor en una casilla conservando su estilo.

    El texto va «en línea» (inlineStr) y no por la tabla de cadenas
    compartidas: así no hay que tocar sharedStrings ni llevar la cuenta de los
    índices, que es donde estos archivos se rompen.
    """
    if valor is None or valor == '':
        return hoja
    patron = re.compile(r'<c r="%s"([^>]*?)(?:/>|>.*?</c>)' % ref, re.S)

    def cambia(m):
        attr = re.sub(r'\s*t="\w+"', '', m.group(1))
        if numero:
            return '<c r="%s"%s><v>%s</v></c>' % (ref, attr, valor)
        return ('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t>'
                '</is></c>' % (ref, attr, _esc(valor)))

    nueva, n = patron.subn(cambia, hoja, count=1)
    if not n:
        raise KeyError(f'el molde no tiene la casilla {ref}')
    return nueva


def app_xml(nombres: list[str]) -> bytes:
    """Rehace docProps/app.xml con las hojas que de verdad tiene el libro.

    Esta pieza lleva la lista de hojas y de rangos con nombre, y Excel la
    compara con el libro al abrirlo: si sobra o falta un nombre, avisa de que
    «encontró un problema con el contenido». LibreOffice ni la mira, así que
    un archivo puede parecer sano y no estarlo.
    """
    tit = ''.join('<vt:lpstr>%s</vt:lpstr>' % _esc(n) for n in nombres)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/'
        '2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/'
        'officeDocument/2006/docPropsVTypes">'
        '<Application>Tablero de emisiones fugitivas</Application>'
        '<ScaleCrop>false</ScaleCrop>'
        '<HeadingPairs><vt:vector size="2" baseType="variant">'
        '<vt:variant><vt:lpstr>Hojas de c\u00e1lculo</vt:lpstr></vt:variant>'
        '<vt:variant><vt:i4>%d</vt:i4></vt:variant>'
        '</vt:vector></HeadingPairs>'
        '<TitlesOfParts><vt:vector size="%d" baseType="lpstr">%s</vt:vector>'
        '</TitlesOfParts>'
        '<LinksUpToDate>false</LinksUpToDate>'
        '<SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged>'
        '<AppVersion>16.0300</AppVersion></Properties>'
        % (len(nombres), len(nombres), tit)).encode('utf-8')


# Lo que cabe en una línea de cada bloque combinado, medido en caracteres a
# partir del ancho de las columnas que abarca: E12:N12 son unos 93, y B24:G25
# unos 59. Sirve para saber cuántas líneas va a ocupar un texto.
ANCHO_DESCRIPCION = 93
ANCHO_ACTIVIDADES = 59


def _alto_fila(hoja: str, fila: int, texto: str, ancho: int,
               filas: int = 1, minimo: float = 25.15) -> str:
    """Hace crecer la fila para que el texto quepa.

    El formato trae las filas con alto fijo, y Excel no ajusta solo cuando las
    celdas están combinadas: un texto de tres líneas se ve cortado a la mitad
    y, al imprimir la ficha, falta justo la parte que explica la fuga.
    """
    if not texto:
        return hoja
    lineas = max(1, -(-len(str(texto)) // ancho))
    alto = max(minimo, lineas * 13.5 + 5) / filas
    return re.sub(r'<row r="%d"([^>]*?)>' % fila,
                  lambda m: '<row r="%d"%s>' % (
                      fila, re.sub(r'ht="[\d.]+"', 'ht="%.2f"' % alto, m.group(1))),
                  hoja, count=1)


def _ancla(a, rid: str, idp: int, nombre: str) -> str:
    c1, o1, f1, r1, c2, o2, f2, r2 = a
    return (
        '<xdr:twoCellAnchor editAs="oneCell">'
        f'<xdr:from><xdr:col>{c1}</xdr:col><xdr:colOff>{o1}</xdr:colOff>'
        f'<xdr:row>{f1}</xdr:row><xdr:rowOff>{r1}</xdr:rowOff></xdr:from>'
        f'<xdr:to><xdr:col>{c2}</xdr:col><xdr:colOff>{o2}</xdr:colOff>'
        f'<xdr:row>{f2}</xdr:row><xdr:rowOff>{r2}</xdr:rowOff></xdr:to>'
        '<xdr:pic><xdr:nvPicPr>'
        f'<xdr:cNvPr id="{idp}" name="{nombre}"/>'
        '<xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr>'
        '</xdr:nvPicPr><xdr:blipFill>'
        '<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/'
        f'2006/relationships" r:embed="{rid}"/>'
        '<a:stretch><a:fillRect/></a:stretch></xdr:blipFill>'
        '<xdr:spPr><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr>'
        '</xdr:pic><xdr:clientData/></xdr:twoCellAnchor>')


def generar(cierres: list[dict], destino: str) -> str:
    z = zipfile.ZipFile(MOLDE)
    piezas = {n: z.read(n) for n in z.namelist()}
    z.close()

    modelo = piezas['xl/worksheets/sheet1.xml'].decode('utf-8')
    dib_modelo = piezas['xl/drawings/drawing1.xml'].decode('utf-8')
    logo = re.search(r'<xdr:twoCellAnchor.*?</xdr:twoCellAnchor>',
                     dib_modelo, re.S).group(0)
    cab_dib = dib_modelo[:dib_modelo.index('<xdr:twoCellAnchor')]

    hojas_xml, rels_wb, overrides = [], [], []
    medios = 2                                    # image1.png es el logo

    for i, c in enumerate(cierres, start=1):
        hoja = modelo
        # ---- identificación
        hoja = _escribir(hoja, 'D5', c['id'])
        hoja = _escribir(hoja, 'K5', serie(c.get('fechaDeteccion')), numero=True)
        hoja = _escribir(hoja, 'D6', c.get('dependencia', 'CRU'))
        hoja = _escribir(hoja, 'K6', c['campo'])
        hoja = _escribir(hoja, 'D7', c.get('tipoFacilidad', 'TANQUE'))
        hoja = _escribir(hoja, 'K7', c['facilidad'])
        hoja = _escribir(hoja, 'D8', c['equipo'])
        hoja = _escribir(hoja, 'K8', c.get('punto', ''))
        hoja = _escribir(hoja, 'D9', c.get('elemento', ''))
        hoja = _escribir(hoja, 'K9', c.get('campana', ''))
        # ---- medición
        hoja = _escribir(hoja, 'D10', c['tasa'], numero=True)
        hoja = _escribir(hoja, 'K10', round(c['gei'], 2), numero=True)
        hoja = _escribir(hoja, 'E12', c.get('hallazgo', ''))
        hoja = _alto_fila(hoja, 12, c.get('hallazgo', ''), ANCHO_DESCRIPCION)
        # ---- cierre; la verificación se deja en blanco a propósito
        hoja = _escribir(hoja, 'B24', c.get('actividades', ''))
        # B24:G25 ocupa dos filas, así que el alto se reparte entre las dos
        for f in (24, 25):
            hoja = _alto_fila(hoja, f, c.get('actividades', ''),
                              ANCHO_ACTIVIDADES, filas=2)
        hoja = _escribir(hoja, 'K23', serie(c.get('fechaCierre')), numero=True)
        if c.get('tasaCierre') is not None:
            hoja = _escribir(hoja, 'K24', c['tasaCierre'], numero=True)

        # ---- las fotos
        anclas, rels_dib = [logo], ['<Relationship Id="rId1" Type="http://'
                                    'schemas.openxmlformats.org/officeDocument/'
                                    '2006/relationships/image" '
                                    'Target="../media/image1.png"/>']
        for k, (campo, ancla, nombre) in enumerate(
                [('fotoInicial', ANCLA_INICIAL, 'Condición inicial'),
                 ('fotoFinal', ANCLA_FINAL, 'Condición final')], start=2):
            foto = c.get(campo)
            if not foto:
                continue
            ext = foto['ext']
            ruta = f'xl/media/image{medios}.{ext}'
            piezas[ruta] = foto['bytes']
            rels_dib.append(
                f'<Relationship Id="rId{k}" Type="http://schemas.'
                'openxmlformats.org/officeDocument/2006/relationships/image" '
                f'Target="../media/image{medios}.{ext}"/>')
            anclas.append(_ancla(ancla, f'rId{k}', 100 + i * 10 + k, nombre))
            medios += 1

        piezas[f'xl/drawings/drawing{i}.xml'] = (
            cab_dib + ''.join(anclas) + '</xdr:wsDr>').encode('utf-8')
        piezas[f'xl/drawings/_rels/drawing{i}.xml.rels'] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships">' + ''.join(rels_dib)
            + '</Relationships>').encode('utf-8')

        piezas[f'xl/worksheets/sheet{i}.xml'] = hoja.encode('utf-8')
        # cada hoja con su propia copia de la configuración de impresión:
        # compartir una sola pieza entre varias hojas es de las cosas que Excel
        # mira con lupa, y no cuesta nada evitarlo
        piezas[f'xl/printerSettings/printerSettings{i}.bin'] = \
            piezas['xl/printerSettings/printerSettings1.bin']
        piezas[f'xl/worksheets/_rels/sheet{i}.xml.rels'] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships">'
            f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/printerSettings" '
            f'Target="../printerSettings/printerSettings{i}.bin"/>'
            f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/drawing" '
            f'Target="../drawings/drawing{i}.xml"/>'
            '</Relationships>').encode('utf-8')

        # el nombre de la pestaña es el ID del punto, como en el archivo suyo
        nombre_hoja = _esc(str(c['id'])[:31]) or f'FICHA {i}'
        # los identificadores arrancan en 101 para no chocar con los que el
        # molde ya usa (estilos, tema, cadenas): si se repite uno, el libro
        # abre pero las hojas apuntan a la pieza equivocada
        rid = f'rId{100 + i}'
        hojas_xml.append(f'<sheet name="{nombre_hoja}" sheetId="{i}" '
                         f'r:id="{rid}"/>')
        rels_wb.append(
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.'
            f'org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>')
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.spreadsheetml.'
            'worksheet+xml"/>'
            f'<Override PartName="/xl/drawings/drawing{i}.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.drawing+xml"/>')

    # ---- el libro: las hojas nuevas en lugar del molde
    wb = piezas['xl/workbook.xml'].decode('utf-8')
    wb = re.sub(r'<sheets>.*?</sheets>', '<sheets>%s</sheets>' % ''.join(hojas_xml),
                wb, flags=re.S)
    # la pestaña activa tiene que existir: si apunta más allá de la última
    # hoja, Excel no abre el archivo
    wb = re.sub(r'firstSheet="\d+"', 'firstSheet="0"', wb)
    wb = re.sub(r'activeTab="\d+"', 'activeTab="0"', wb)
    piezas['xl/workbook.xml'] = wb.encode('utf-8')

    rels = piezas['xl/_rels/workbook.xml.rels'].decode('utf-8')
    rels = re.sub(r'<Relationship\s[^>]*?Target="worksheets/sheet1\.xml"[^>]*/>',
                  ''.join(rels_wb), rels)
    piezas['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')

    ct = piezas['[Content_Types].xml'].decode('utf-8')
    ct = re.sub(r'<Override PartName="/xl/worksheets/sheet1\.xml"[^>]*/>', '', ct)
    ct = re.sub(r'<Override PartName="/xl/drawings/drawing1\.xml"[^>]*/>', '', ct)
    ct = ct.replace('</Types>', ''.join(overrides) + '</Types>')
    piezas['[Content_Types].xml'] = ct.encode('utf-8')

    # la hoja y el dibujo del molde ya no van: se reemplazaron por las fichas
    if len(cierres) >= 1:
        for sobra in ('xl/worksheets/sheet1.xml', 'xl/drawings/drawing1.xml',
                      'xl/worksheets/_rels/sheet1.xml.rels',
                      'xl/drawings/_rels/drawing1.xml.rels'):
            if sobra in piezas and not any(
                    sobra.endswith(f'sheet{i}.xml') or sobra.endswith(f'drawing{i}.xml')
                    or sobra.endswith(f'sheet{i}.xml.rels')
                    or sobra.endswith(f'drawing{i}.xml.rels')
                    for i in range(1, len(cierres) + 1)):
                del piezas[sobra]

    piezas['docProps/app.xml'] = app_xml(
        [re.search(r'name="([^"]*)"', h).group(1) for h in hojas_xml])

    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as out:
        for nombre, datos in piezas.items():
            out.writestr(nombre, datos)
    return destino
