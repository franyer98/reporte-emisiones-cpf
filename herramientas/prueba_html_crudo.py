# -*- coding: utf-8 -*-
"""Con el JavaScript apagado, la página no puede mostrar ninguna cifra."""
import re, io
s = io.open('/home/claude/work/bd/repo/index.html', encoding='utf-8').read()
i = s.index('<div class="tabs-bar">')
j = s.index('</section>', s.index('id="kpiCSPuntos"'))
trozo = s[i:j]
malas = [(k, v.strip()) for k, v in re.findall(r'id="(kpi\w+|tabN\d)"[^>]*>([^<]{1,60})', trozo)
         if re.search(r'\d', v)]
print('  huecos con cifra escrita a mano:', malas or 'ninguno')
# y que no se cuele ninguno de los totales de ejemplo en el HTML visible
for n in ['58.059', '14,447', '45.959', '12.100', '64.092', '15.112']:
    if n in trozo:
        print(f'  >>> MAL: «{n}» sigue escrito en la página')
print('  revisión del encabezado y las tarjetas: terminada')
