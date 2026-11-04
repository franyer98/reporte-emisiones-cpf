# -*- coding: utf-8 -*-
"""La barra de avance debe hablar la misma unidad que la curva."""
import asyncio, threading, http.server
from playwright.async_api import async_playwright
RAIZ='/home/claude/work/bd/repo'
class M(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=RAIZ,**k)
    def do_GET(s):
        if s.path.startswith('/api/'):
            s.send_response(404); s.send_header('content-length','0'); s.end_headers(); return
        return super().do_GET()
    def log_message(s,*a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8907),M).serve_forever,daemon=True).start()
ABIERTOS=[('CPF-1-022','TK-904','ALMACENAMIENTO',240,1),('CPF-1-023','TK-906-B','ALMACENAMIENTO',67,1),
 ('CPF-2-016','300-TK-0201','PROCESOS',1100,2),('CPF-2-017','300-TK-0101','PROCESOS',510,2),
 ('CEN-008','ETK-1161-B','SKIM TANK',2400,3)]
CERRADOS=[('CPF-1-030','TK-901B','FWKOS',17700,1,'2026-09-28'),
 ('CPF-2-031','300-TK-0103','ALMACENAMIENTO',6470,2,'2026-10-13'),
 ('CEN-032','ETK-1101-B','FWKOS',4300,3,'2026-10-20')]
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':900})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8907/'); await pg.wait_for_timeout(3500)
        await pg.evaluate("""([ab,ce])=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          CERRADAS1.length=0;CERRADAS2.length=0;CERRADASCS.length=0;
          ab.forEach((x,i)=>{const d={id:'a'+i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
            elemento:'Empaque',img:'',estado:'abierto',fechaDeteccion:'2026-06-15'};
            (x[4]===1?DATA1:x[4]===2?DATA2:DATACS).push(d);});
          ce.forEach((x,i)=>{const d={id:'c'+i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
            elemento:'Empaque',img:'',imgCierre:'x',estado:'cerrado',
            fechaDeteccion:'2026-06-15',fechaCierre:x[5]};
            (x[4]===1?CERRADAS1:x[4]===2?CERRADAS2:CERRADASCS).push(d);});
          refrescarTodo();}""", [ABIERTOS,CERRADOS])
        await pg.wait_for_timeout(1200)
        leer=lambda: pg.evaluate("""()=>({
          pct:(document.getElementById('pgPct')||{}).textContent,
          elim:(document.getElementById('pgElimG')||{}).textContent,
          act:(document.getElementById('pgActivaG')||{}).textContent,
          barra:(document.getElementById('pgRel')||{style:{}}).style.width,
          uni:(document.querySelector('[data-uni].active')||{}).textContent})""")
        mal=[]
        for etiqueta in ['g/Hr','ton CO₂eq']:
            await pg.evaluate("""(t)=>{const b=[...document.querySelectorAll('[data-uni]')]
              .find(x=>x.textContent.trim()===t); if(b) b.click();}""", etiqueta)
            await pg.wait_for_timeout(700)
            r=await leer()
            print(f"  unidad «{r['uni']}»  ·  {r['pct']} eliminado  ·  barra {r['barra']}")
            print(f"     Eliminada {r['elim']}   ·   Activa {r['act']}")
            esperado = 'ton CO₂eq/año' if etiqueta=='ton CO₂eq' else 'g/Hr'
            for campo in ('elim','act'):
                if not r[campo].endswith(esperado): mal.append(f"{campo} dice «{r[campo]}» con unidad {etiqueta}")
        print('  desajustes:', mal or 'ninguno')
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
