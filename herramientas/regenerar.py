"""Rehace el molde y el ejemplo, y comprueba las dos cosas que Excel mira."""
import re, sys, zipfile
sys.path.insert(0, '/home/claude/cierres')
import molde, fichas

molde.construir()
z = zipfile.ZipFile('/home/claude/cierres/GOP-F-007.xlsx')
ini = {'bytes': z.read('xl/media/image2.jpeg'), 'ext': 'jpeg'}
fin = {'bytes': z.read('xl/media/image3.png'), 'ext': 'png'}
base = dict(campo='CAMPO RUBIALES', facilidad='CPF-2', campana='2026',
            fechaDeteccion='2026-06-15', fechaCierre='2026-09-28',
            tasaCierre=0, fotoInicial=ini, fotoFinal=fin)
C = [dict(base, id='EFRB-CPF-2-013', equipo='300-TK-0103', punto='ESCOTILLA',
          elemento='EMPAQUE EN MAL ESTADO', tasa=2800, gei=2800 * 0.2226457,
          hallazgo='Se evidencia emisión fugitiva en la escotilla del tanque '
                   '300-TK-0103. Tasa medida con cámara OGI/FLIR: 2.800 g/Hr.',
          actividades='Se realiza cambio de empaquetadura en la escotilla y '
                      'ajuste de pernos.'),
     dict(base, id='EFRB-CPF-2-014', equipo='300-TK-0201', punto='MANHOLE',
          elemento='EMPAQUE EN MAL ESTADO', tasa=1900, gei=1900 * 0.2360923,
          hallazgo='Se evidencia emisión fugitiva en el manhole del tanque '
                   '300-TK-0201. Tasa medida con cámara OGI/FLIR: 1.900 g/Hr.',
          actividades='Se realiza cambio de empaquetadura del manhole.'),
     dict(base, id='EFRB-CPF-2-015', equipo='300-TK-0301', punto='ESCOTILLA',
          elemento='EMPAQUE', tasa=540, gei=540 * 0.2432246,
          hallazgo='Se evidencia emisión fugitiva en la escotilla del tanque '
                   '300-TK-0301. Tasa medida con cámara OGI/FLIR: 540 g/Hr.',
          actividades='Se realiza cambio de empaquetadura en la escotilla.')]
fichas.generar(C, '/home/claude/cierres/GOP-F-007-ejemplo.xlsx')


def revisar(ruta):
    z = zipfile.ZipFile(ruta)
    wb = z.read('xl/workbook.xml').decode()
    hojas = re.findall(r'<sheet name="([^"]*)"[^>]*r:id="(\w+)"', wb)
    rels = dict(re.findall(r'Id="(\w+)"[^>]*Target="([^"]+)"',
                           z.read('xl/_rels/workbook.xml.rels').decode()))
    act = re.search(r'activeTab="(\d+)"', wb)
    app = re.findall(r'<vt:lpstr>([^<]*)</vt:lpstr>',
                     z.read('docProps/app.xml').decode())[1:]
    fallos = []
    if act and int(act.group(1)) >= len(hojas):
        fallos.append(f'activeTab={act.group(1)} y sólo hay {len(hojas)} hojas')
    if app != [h for h, _ in hojas]:
        fallos.append('app.xml no lista las mismas hojas')
    for nom, rid in hojas:
        if rid not in rels:
            fallos.append(f'la hoja «{nom}» apunta a {rid}, que no existe')
        elif 'xl/' + rels[rid] not in z.namelist():
            fallos.append(f'falta la pieza de «{nom}»')
    # cada pieza XML tiene que ser XML bien formado: una sin su etiqueta raíz
    # pasa todas las comprobaciones de arriba y aun así rompe el archivo
    from xml.etree import ElementTree
    for n in z.namelist():
        if n.endswith('.xml') or n.endswith('.rels'):
            try:
                ElementTree.fromstring(z.read(n))
            except Exception as e:
                fallos.append(f'{n} no es XML válido: {e}')
    ct = z.read('[Content_Types].xml').decode()
    for n in z.namelist():
        if n.endswith('.xml') and n.startswith('xl/worksheets/sheet'):
            if '/' + n not in ct:
                fallos.append(f'{n} no está declarada en [Content_Types]')
    print(f'  {ruta.split("/")[-1]:26} {len(hojas)} hoja(s) · '
          + ('TODO BIEN' if not fallos else 'MAL: ' + '; '.join(fallos)))


revisar('/home/claude/cierres/GOP-F-007-molde.xlsx')
revisar('/home/claude/cierres/GOP-F-007-ejemplo.xlsx')
