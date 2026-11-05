# -*- coding: utf-8 -*-
"""Las fichas de cierre deben quedar alineadas entre columnas."""
import asyncio, threading, http.server, base64, io
from playwright.async_api import async_playwright
RAIZ='/home/claude/work/bd/repo'
class M(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=RAIZ,**k)
    def do_GET(s):
        if s.path.startswith('/api/'):
            s.send_response(404); s.send_header('content-length','0'); s.end_headers(); return
        return super().do_GET()
    def log_message(s,*a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8972),M).serve_forever,daemon=True).start()

def png(w,h,c):
    """Una imagen de las medidas pedidas, para probar proporciones distintas."""
    import zlib,struct
    cruda=b''.join(b'\x00'+bytes(c)*w for _ in range(h))
    def trozo(t,d):
        return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    datos=(b'\x89PNG\r\n\x1a\n'
      +trozo(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
      +trozo(b'IDAT',zlib.compress(cruda))+trozo(b'IEND',b''))
    return 'data:image/png;base64,'+base64.b64encode(datos).decode()

async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':1000})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8972/'); await pg.wait_for_timeout(3400)
        # cuatro cierres con fotos de proporciones MUY distintas y textos de
        # distinto largo: así se ve si las fichas se desalinean
        fotos=[(640,480,(90,90,90)),(640,360,(120,120,120)),
               (480,640,(70,70,70)),(800,300,(140,140,140))]
        datos=[]
        for i,(w,h,c) in enumerate(fotos):
            datos.append({'id':100+i,'punto':f'CPF-1-0{i+1}','equipo':f'TK-90{i+1}',
              'area':'PROCESOS','elemento':'Empaque','tasa':9300-i*2000,
              'hallazgo':'Manhole asegurado con solo 2 pernos (faltan pernos).' if i%2==0 else 'Corta.',
              'img':png(w,h,c),'imgCierre':png(w,h,(30,30,30)),'tasaCierre':0,
              'estado':'cerrado','fechaDeteccion':'2026-06-15','fechaCierre':'2026-10-15',
              'fid':f'CPF-1-0{i+1}'})
        await pg.evaluate("""(ce)=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          CERRADAS1.length=0;CERRADAS2.length=0;CERRADASCS.length=0;
          ce.forEach(d=>CERRADAS1.push(d));
          refrescarTodo();}""", datos)
        await pg.wait_for_timeout(900)
        await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.tab')]
          .find(x=>x.textContent.trim().startsWith('Cierres')); if(b) b.click();}""")
        await pg.wait_for_timeout(1800)
        r=await pg.evaluate("""()=>{
          const cs=[...document.querySelectorAll('#ciCuerpo .card')];
          return cs.map(c=>{
            const f=c.querySelector('.card-photo'), b=c.querySelector('.card-body');
            const eq=c.querySelector('.card-eq');
            const im=c.querySelector('.card-photo img');
            return {eq:(eq||{}).textContent, alto:Math.round(c.getBoundingClientRect().height),
                    foto:f?Math.round(f.getBoundingClientRect().height):-1,
                    anchoFicha:Math.round(c.getBoundingClientRect().width),
                    anchoFoto:f?Math.round(f.getBoundingClientRect().width):-1,
                    anchoImg:im?Math.round(im.getBoundingClientRect().width):-1,
                    cuerpoY:b?Math.round(b.getBoundingClientRect().top - c.getBoundingClientRect().top):-1};});}""")
        huecos=[]
        for x in r:
            hueco=x['anchoFicha']-x['anchoImg']
            print(f"  {str(x['eq'])[:16]:18} ficha {x['anchoFicha']:4}x{x['alto']:<4} px ·"
                  f" foto {x['anchoFoto']:4} px · imagen {x['anchoImg']:4} px ·"
                  f" franja muerta {hueco:4} px")
            if hueco>4: huecos.append(x['eq'])
        print('  fichas con franja muerta:', huecos or 'ninguna')
        fotos_h=sorted(set(x['foto'] for x in r))
        cuerpos=sorted(set(x['cuerpoY'] for x in r))
        print('  alturas de foto distintas:', fotos_h if len(fotos_h)>1 else 'no, todas iguales')
        print('  el texto arranca a distinta altura:', cuerpos if len(cuerpos)>1 else 'no, todas iguales')
        el=await pg.query_selector('#ciCuerpo .grid')
        if el: await el.screenshot(path='cierres.png')
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
