# -*- coding: utf-8 -*-
"""Cada fila de prioridad debe llevar su equivalente, y sumar el de la facilidad."""
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
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8921),M).serve_forever,daemon=True).start()
REAL=[('CPF-1-022','TK-904','ALMACENAMIENTO',240,1),('CPF-1-023','TK-906-B','ALMACENAMIENTO',67,1),
 ('CPF-2-016','300-TK-0201','PROCESOS',1100,2),('CPF-2-017','300-TK-0101','PROCESOS',510,2),
 ('CEN-008','ETK-1161-B','SKIM TANK',2400,3),('CEN-009','ETK-1101-B','FWKOS',1100,3)]
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':900})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8921/'); await pg.wait_for_timeout(3500)
        await pg.evaluate("""(real)=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          real.forEach((x,i)=>{const d={id:'p'+i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
            elemento:'Empaque',img:'',estado:'abierto',fechaDeteccion:'2026-09-12'};
            (x[4]===1?DATA1:x[4]===2?DATA2:DATACS).push(d);});
          refrescarTodo();}""", REAL)
        await pg.wait_for_timeout(1000)
        for tab,cont,fac in [('CPF-1','prio1','CPF-1'),('CPF-2','prio2','CPF-2'),('Caño Sur','prio3','CAÑO SUR')]:
            await pg.evaluate("""(t)=>{const b=[...document.querySelectorAll('.tab')]
              .find(x=>x.textContent.trim().startsWith(t)); if(b) b.click();}""", tab)
            await pg.wait_for_timeout(800)
            r=await pg.evaluate("""([c,f])=>{
              const filas=[...document.querySelectorAll('#'+c+' .prio-row')].map(x=>({
                eq:(x.querySelector('.prio-eq')||{}).textContent,
                val:(x.querySelector('.prio-val')||{}).textContent,
                co2:(x.querySelector('.prio-co2')||{}).textContent}));
              const datos = f==='CPF-1'?DATA1:f==='CPF-2'?DATA2:DATACS;
              return {filas, esperado: co2eqDe(datos, f)};}""", [cont,fac])
            suma=sum(float(x['co2'].split(' ')[0].replace('.','').replace(',','.')) for x in r['filas'] if x['co2'])
            print(f"  [{tab}]")
            for x in r['filas']: print(f"     {x['eq']:16} {x['val']:>14}   {x['co2']}")
            d=abs(suma-r['esperado'])
            print(f"     suma {suma:.2f}  ·  facilidad {r['esperado']:.2f}  ·  dif {d:+.2f}"
                  f"  {'OK' if d<0.02 else '>>> MAL'}")
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
