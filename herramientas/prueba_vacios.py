# -*- coding: utf-8 -*-
"""Un punto sin descripción o sin elemento no debe escribir «undefined»."""
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
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8961),M).serve_forever,daemon=True).start()
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':900})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8961/'); await pg.wait_for_timeout(3500)
        # un punto completo y otro al que le faltan campos, como se guarda con prisa
        await pg.evaluate("""()=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          DATA1.push({id:1,punto:'CPF-1-022',equipo:'TK-904',area:'ALMACENAMIENTO',
            tasa:240,elemento:'Empaque',hallazgo:'Fuga en el empaque del manhole.',
            img:'',estado:'abierto',fechaDeteccion:'2026-09-12'});
          DATA1.push({id:2,punto:'CPF-1-023',equipo:'TK-906-B',area:'ALMACENAMIENTO',
            tasa:67,img:'',estado:'abierto',fechaDeteccion:'2026-09-12'});
          refrescarTodo();}""")
        await pg.wait_for_timeout(1200)
        await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.tab')]
          .find(x=>x.textContent.trim().startsWith('CPF-1')); if(b) b.click();}""")
        await pg.wait_for_timeout(900)
        txt=await pg.evaluate("()=>document.body.innerText")
        # y la ficha ampliada del punto incompleto
        await pg.evaluate("""()=>{const c=[...document.querySelectorAll('#grid1 .card')]
          .find(x=>x.innerText.includes('TK-906-B')); if(c) c.click();}""")
        await pg.wait_for_timeout(700)
        ficha=await pg.evaluate("""()=>{const l=document.getElementById('lightbox');
          return l&&l.classList.contains('open')?l.innerText:'(no abrió)'}""")
        print('  ficha ampliada:', ' | '.join(x for x in ficha.split('\n') if x.strip())[:150])
        malos=[]
        if 'undefined' in txt: malos.append('la página escribe «undefined»')
        if 'undefined' in ficha: malos.append('la ficha escribe «undefined»')
        if 'null' in txt: malos.append('la página escribe «null»')
        print('  fallos:', malos or 'ninguno')
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
