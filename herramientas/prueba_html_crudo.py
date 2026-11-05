# -*- coding: utf-8 -*-
"""Con el JavaScript apagado, la página no puede mostrar ninguna cifra.

Lee el HTML tal como lo sirve el servidor, SIN ejecutarlo. Es la única forma de
ver lo que hay escrito a mano en el marcado: cualquier prueba con navegador lo
reemplaza al arrancar y no se entera. Así se cazaron en su día los datos de
ejemplo que seguían impresos en la página.

Antes se anclaba en «id=kpiCSPuntos» para delimitar el trozo. Ese hueco se
retiró con las tarjetas de facilidad y la prueba reventaba con ValueError —el
corredor viejo lo daba por bueno—. Ahora recorre el documento entero, que es
más estricto y no depende de que exista ningún id en particular.
"""
import re, io, sys

RUTA = '/home/claude/work/bd/repo/index.html'
s = io.open(RUTA, encoding='utf-8').read()
malo = []

# 1) ningún hueco que el código rellena puede traer ya un número escrito
for k, v in re.findall(r'id="(kpi\w+|tabN\d|pg\w+|intro\w+)"[^>]*>([^<]{1,80})', s):
    # las entidades («&#8592;» para una flecha) llevan dígitos que no son cifras
    limpio = re.sub(r'&#?\w+;', '', v).strip()
    if re.search(r'\d', limpio) and limpio not in ('—', '-'):
        malo.append(f'«{k}» trae escrito «{limpio}»')

# 2) ningún total de ejemplo de los que alguna vez estuvieron impresos
for n in ['58.059', '14,447', '45.959', '12.100', '64.092', '15.112',
          '1.312,92', '1.312,17', '7.262', '62.070', '15.003,50']:
    # sólo cuenta si está en el marcado visible, no dentro del código ni de los
    # comentarios, donde aparece legítimamente al explicar por qué se quitó
    for m in re.finditer(re.escape(n), s):
        ini = s.rfind('>', 0, m.start()); fin = s.find('<', m.start())
        if ini == -1 or fin == -1: continue
        trozo = s[ini+1:fin]
        dentro_script = s.rfind('<script', 0, m.start()) > s.rfind('</script>', 0, m.start())
        if not dentro_script and n in trozo:
            malo.append(f'«{n}» sigue impreso en la página')

print('  cifras escritas a mano en el marcado:', malo or 'ninguna')
if malo: sys.exit(1)
