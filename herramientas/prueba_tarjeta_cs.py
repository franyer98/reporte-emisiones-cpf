# -*- coding: utf-8 -*-
"""Caño Sur: sus cifras tienen que cuadrar con sus datos, y en su pestaña no
debe quedar ninguna tarjeta de facilidad.

Antes esta prueba miraba las tarjetas kpiCS*/fcard.f1/fcard.f2, que se
retiraron. Hacía getComputedStyle(null) y reventaba — y el corredor viejo lo
reportaba como «salida 0», así que llevaba tandas en rojo sin que se notara.
Ahora comprueba donde viven de verdad esas cifras: el encabezado y el reparto
de la tarjeta Total.
"""
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
threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',8879),M).serve_forever,daemon=True).start()

CS=[('CEN-008','ETK-1161-B','SKIM TANK',2400),('CEN-009','ETK-1101-B','FWKOS',1100),
    ('CEN-010','ETK-1161-B','SKIM TANK',660),('CEN-011','ETK-1101-C','FWKOS',13)]

def num(t):
    import re
    m=re.search(r'[\d.]+(?:,\d+)?', t or '')
    return float(m.group(0).replace('.','').replace(',','.')) if m else None

async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':900})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8879/'); await pg.wait_for_timeout(3400)
        await pg.evaluate("""(cs)=>{
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          DATA1.push({id:90,punto:'CPF-1-022',equipo:'TK-904',area:'ALMACENAMIENTO',
            tasa:240,elemento:'Empaque',hallazgo:'x',img:'',estado:'abierto',
            fechaDeteccion:'2026-09-12'});
          cs.forEach((x,i)=>DATACS.push({id:i,punto:x[0],equipo:x[1],area:x[2],tasa:x[3],
            elemento:'Empaque',hallazgo:'x',img:'',estado:'abierto',
            fechaDeteccion:'2026-09-12'}));
          refrescarTodo();}""", CS)
        await pg.wait_for_timeout(1000)
        malos=[]

        # --- 1. el reparto de la tarjeta Total, en «Todas»
        rep=await pg.evaluate("""()=>{
          const f=[...document.querySelectorAll('#kpiTotReparto .fcard-row')]
            .find(r=>((r.querySelector('.fr-cab span')||{}).textContent||'')
                      .trim().toUpperCase()==='CAÑO SUR');
          return f?{pts:(f.querySelector('.pts')||{}).textContent,
                    gh:(f.querySelector('.fr-gh')||{}).textContent,
                    ton:(f.querySelector('.fcard-co2')||{}).textContent}:null;}""")
        verdad=await pg.evaluate("()=>({n:DATACS.length,"
                                 "g:DATACS.reduce((a,x)=>a+x.tasa,0),c:co2eqDe(DATACS,'CAÑO SUR')})")
        print(f"  datos: {verdad['n']} puntos · {verdad['g']:,.0f} g/Hr · {verdad['c']:,.2f} ton"
              .replace(',','.'))
        if not rep: malos.append('Caño Sur no sale en el reparto')
        else:
            print(f"  reparto: {rep['pts']} · {rep['gh']} · {rep['ton']}")
            if num(rep['pts'])!=verdad['n']: malos.append('puntos del reparto')
            if num(rep['gh'])!=verdad['g']:  malos.append('g/Hr del reparto')
            if abs(num(rep['ton'])-verdad['c'])>0.02: malos.append('CO2eq del reparto')

        # --- 2. su pestaña: encabezado correcto y sin tarjetas
        await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.tab')]
          .find(x=>x.textContent.trim().startsWith('Caño Sur')); if(b) b.click();}""")
        await pg.wait_for_timeout(1000)
        enc=await pg.evaluate("""()=>({
          tasa:(document.getElementById('kpiTotal')||{}).textContent,
          co2:(document.getElementById('kpiCo2')||{}).textContent,
          fila:(()=>{const f=document.querySelector('.facility-row');
                     return f?Math.round(f.getBoundingClientRect().height):-1})(),
          tarjetas:[...document.querySelectorAll('.facility-row .fcard')]
                     .filter(e=>e.offsetParent!==null).length})""")
        print(f"  pestaña Caño Sur: {enc['tasa']} · {enc['co2']} ton"
              f" · alto de la fila {enc['fila']} px · {enc['tarjetas']} tarjeta(s)")
        if num(enc['tasa'])!=verdad['g']: malos.append('tasa del encabezado')
        if abs(num(enc['co2'])-verdad['c'])>0.02: malos.append('CO2eq del encabezado')
        if enc['fila']!=0: malos.append('la fila de tarjetas no está oculta')
        if enc['tarjetas']!=0: malos.append('quedan tarjetas visibles')

        print('  fallos:', malos or 'ninguno')
        print('  errores:', errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
