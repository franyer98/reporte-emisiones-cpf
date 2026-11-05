# -*- coding: utf-8 -*-
"""El pie dice la campaña entera y nombra sólo las facilidades que existen."""
import asyncio, threading, http.server, os
from playwright.async_api import async_playwright
RAIZ='/home/claude/work/bd/repo'
class M(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=RAIZ,**k)
    def do_GET(s):
        if s.path.startswith('/api/'):
            s.send_response(404); s.send_header('content-length','0'); s.end_headers(); return
        return super().do_GET()
    def log_message(s,*a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8993),M).serve_forever,daemon=True).start()

def num(t):
    import re
    m=re.search(r'[\d.]+(?:,\d+)?', t or '')
    return float(m.group(0).replace('.','').replace(',','.')) if m else None

async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':1000})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8993/'); await pg.wait_for_timeout(3400)
        # sin Caño Sur a propósito: el pie NO debe nombrarlo
        await pg.evaluate("""()=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          CERRADAS1.length=0;CERRADAS2.length=0;CERRADASCS.length=0;
          const p=(id,pt,eq,ar,t)=>({id,punto:pt,equipo:eq,area:ar,tasa:t,elemento:'Empaque',
            hallazgo:'x',img:'',estado:'abierto',fechaDeteccion:'2026-06-15'});
          DATA1.push(p(1,'CPF-1-022','TK-904','ALMACENAMIENTO',240));
          DATA2.push(p(2,'CPF-2-016','300-TK-0201','PROCESOS',1100));
          const c=p(3,'CPF-1-030','TK-901B','FWKOS',17700);
          c.estado='cerrado'; c.fechaCierre='2026-10-15'; c.imgCierre='x'; c.tasaCierre=0;
          CERRADAS1.push(c);
          refrescarTodo();}""")
        await pg.wait_for_timeout(1200)
        r=await pg.evaluate("""()=>{
          const t=[...document.querySelectorAll('#pieTira .pie-cel')].map(c=>({
            k:(c.querySelector('.k')||{}).textContent,
            n:(c.querySelector('.n')||{}).textContent,
            u:(c.querySelector('.u')||{}).textContent}));
          return {celdas:t, meta:(document.getElementById('pieMeta')||{}).textContent,
                  verdad:{abierto:co2eqDe(DATA1,'CPF-1')+co2eqDe(DATA2,'CPF-2')+co2eqDe(DATACS,'CAÑO SUR'),
                          elim:CERRADAS1.reduce((a,d)=>a+d.tasa*kDe('CPF-1',d.area,d.equipo,d.punto),0),
                          n:DATA1.length+DATA2.length+DATACS.length+CERRADAS1.length}};}""")
        for c in r['celdas']: print(f"  {c['k']:12} {c['n']:>12}  {c['u']}")
        print('  meta:', r['meta'])
        v=r['verdad']; malos=[]
        d={c['k']:c['n'] for c in r['celdas']}
        if num(d.get('Medido'))!=v['n']: malos.append('puntos medidos')
        if abs(num(d.get('Abierto',''))-v['abierto'])>0.02: malos.append('abierto')
        if abs(num(d.get('Eliminado',''))-v['elim'])>0.02: malos.append('eliminado')
        if 'CAÑO SUR' in (r['meta'] or ''): malos.append('nombra Caño Sur sin tener puntos')
        if 'CPF-1' not in (r['meta'] or '') or 'CPF-2' not in (r['meta'] or ''):
            malos.append('no nombra las facilidades que sí tienen puntos')
        if 'VERSIÓN' not in (r['meta'] or '') or '__SELLO__' in (r['meta'] or ''):
            malos.append('el sello de versión no quedó')
        print('  fallos:', malos or 'ninguno')
        print('  errores:', errs[:3] or 'ninguno')
        el=await pg.query_selector('footer')
        if el: await el.screenshot(path='pie_final.png')
        await nav.close()
        if malos: raise SystemExit(1)
asyncio.run(main())
