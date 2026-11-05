# -*- coding: utf-8 -*-
"""Nada de lo que flota sobre el mapa 3D debe solaparse con otra cosa."""
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
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8941),M).serve_forever,daemon=True).start()
REAL=[('CPF-1-022','TK-904','ALMACENAMIENTO',240,1),('CPF-1-023','TK-906-B','ALMACENAMIENTO',67,1),
 ('CPF-2-016','300-TK-0201','PROCESOS',1100,2),('CEN-008','ETK-1161-B','SKIM TANK',2400,3),
 ('CEN-009','ETK-1101-B','FWKOS',1100,3)]
JS = """([sel])=>{
  const w=document.querySelectorAll('.mapa3d-wrap');
  const vis=[...w].find(x=>x.offsetParent!==null);
  if(!vis) return null;
  const q=c=>vis.querySelector(c);
  const caja=e=>{if(!e||e.offsetParent===null)return null;const r=e.getBoundingClientRect();
                 return r.width&&r.height?{x:r.left,y:r.top,w:r.width,h:r.height}:null;};
  const piezas={total:caja(q('.total3d')), pastilla:caja(q('.m3d-pastilla')),
                vistas:caja(q('.view3d-bar')), zoom:caja(q('.zoom3d'))};
  const choca=(a,b)=>a&&b&&!(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y);
  const nom=Object.keys(piezas); const malos=[];
  for(let i=0;i<nom.length;i++) for(let j=i+1;j<nom.length;j++)
    if(choca(piezas[nom[i]],piezas[nom[j]])) malos.push(nom[i]+' se pisa con '+nom[j]);
  return {piezas, malos};}"""
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        malos=[]
        for ancho,alto,movil in [(1280,900,False),(412,900,True),(360,800,True)]:
            ctx=await nav.new_context(viewport={'width':ancho,'height':alto},
                                      is_mobile=movil,has_touch=movil)
            pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://127.0.0.1:8941/'); await pg.wait_for_timeout(3500)
            await pg.evaluate("""(real)=>{DATA1.length=0;DATA2.length=0;DATACS.length=0;
              real.forEach((x,i)=>{const d={id:'p'+i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
                elemento:'Empaque',img:'',estado:'abierto',fechaDeteccion:'2026-09-12'};
                (x[4]===1?DATA1:x[4]===2?DATA2:DATACS).push(d);});refrescarTodo();}""", REAL)
            for tab in ['CPF-1','Caño Sur']:
                await pg.evaluate("""(t)=>{const b=[...document.querySelectorAll('.tab')]
                  .find(x=>x.textContent.trim().startsWith(t)); if(b) b.click();}""", tab)
                await pg.wait_for_timeout(800)
                await pg.evaluate("()=>{const c=document.querySelector('.mapa3d-wrap');"
                                  "if(c) c.scrollIntoView({block:'center'});}")
                await pg.wait_for_timeout(2500)
                r=await pg.evaluate(JS,[None])
                if not r: print(f"  {ancho}px [{tab}] (sin mapa visible)"); continue
                print(f"  {ancho}px [{tab:9}] {r['malos'] or 'nada se pisa'}")
                malos += [f"{ancho}px {tab}: {m}" for m in r['malos']]
            await ctx.close()
        print('  solapes:', malos or 'ninguno')
        await nav.close()
asyncio.run(main())
