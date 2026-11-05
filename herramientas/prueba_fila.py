# -*- coding: utf-8 -*-
"""La fila de tarjetas no debe dejar hueco, haya una o cuatro visibles."""
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
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8912),M).serve_forever,daemon=True).start()
LIBRO={'CPF-1-022':240,'CPF-1-023':67,'CPF-1-024':53,'CPF-1-025':19,
 'CPF-2-016':1100,'CPF-2-017':510,'CPF-2-018':300,'CPF-2-019':280,
 'CPF-2-020':270,'CPF-2-021':250,'CEN-008':2400,'CEN-009':1100,
 'CEN-010':660,'CEN-011':13}
REAL=[('CPF-1-022','TK-904','ALMACENAMIENTO',1),('CPF-1-023','TK-906-B','ALMACENAMIENTO',1),
 ('CPF-1-024','HEAD-TK-902','PROCESOS',1),('CPF-1-025','HEAD TK 0902','PROCESOS',1),
 ('CPF-2-016','300-TK-0201','PROCESOS',2),('CPF-2-017','300-TK-0101','PROCESOS',2),
 ('CPF-2-018','300-TK-0101','PROCESOS',2),('CPF-2-019','300-TK-0401','FWKOS',2),
 ('CPF-2-020','300-TK-0101','FWKOS',2),('CPF-2-021','300-TK-0201','FWKOS',2),
 ('CEN-008','ETK-1161-B','SKIM TANK',3),('CEN-010','ETK-1161-B','SKIM TANK',3),
 ('CEN-009','ETK-1101-B','FWKOS',3),('CEN-011','ETK-1101-C','FWKOS',3)]
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        ctx=await nav.new_context(viewport={'width':1366,'height':768})
        pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8912/'); await pg.wait_for_timeout(3500)
        datos=[[c,eq,ar,LIBRO[c],f] for c,eq,ar,f in REAL]
        await pg.evaluate("""(real)=>{
          const mk=(x,i)=>({id:'p'+i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
            elemento:'Empaque',img:'',estado:'abierto',fechaDeteccion:'2026-09-12'});
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          real.forEach((x,i)=>{const d=mk(x,i);(x[4]===1?DATA1:x[4]===2?DATA2:DATACS).push(d);});
          refrescarTodo();}""", datos)
        await pg.evaluate("document.querySelectorAll('[class*=aviso]').forEach(e=>e.remove())")
        for etq in ['Todas','CPF-1','CPF-2','Caño Sur']:
            await pg.evaluate("""(t)=>{const b=[...document.querySelectorAll('.tab')]
              .find(x=>x.textContent.trim().startsWith(t)); if(b) b.click();}""", etq)
            await pg.wait_for_timeout(900)
            r=await pg.evaluate("""()=>{
              const fila=document.querySelector('.facility-row');
              const v=[...fila.querySelectorAll('.fcard')].filter(e=>e.offsetParent!==null);
              const ancho=fila.getBoundingClientRect().width;
              const usado=v.reduce((a,e)=>a+e.getBoundingClientRect().width,0)+14*(v.length-1);
              return {n:v.length, ancho:Math.round(ancho), usado:Math.round(usado),
                      hueco:Math.round(ancho-usado)};}""")
            print(f"  [{etq:9}] {r['n']} tarjeta(s) · fila {r['ancho']} px · usan {r['usado']} px · hueco {r['hueco']} px")
            alto=await pg.evaluate("()=>{const f=document.querySelector('.facility-row');"
                 "return f?Math.round(f.getBoundingClientRect().height):-1}")
            print(f"            alto de la fila: {alto} px")
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
