"""Revisa que cada tarjeta del encabezado sume lo que dice su rótulo."""
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
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8857),M)
threading.Thread(target=srv.serve_forever,daemon=True).start()
async def main():
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        pg=await (await nav.new_context(viewport={'width':1280,'height':1000})).new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8857/'); await pg.wait_for_timeout(3200)
        await pg.evaluate("document.getElementById('introSaltar').click()")
        await pg.wait_for_timeout(1600)
        # el tablero ya no pinta los datos de ejemplo, así que la prueba
        # pone los suyos, igual que haría una carga del servidor
        await pg.evaluate("""()=>{
          const mk=(fid,eq,ar,pu,el,t)=>({id:fid,fid:fid,area:ar,equipo:eq,punto:pu,
            elemento:el,tasa:t,hallazgo:'Fuga en '+pu+' de '+eq+'.',img:'',
            estado:'abierto'});
          DATA1.length=0;DATA2.length=0;DATACS.length=0;
          DATA1.push(mk('EFRB-CPF-1-022','TK-904','ALMACENAMIENTO','ESCOTILLA','EMPAQUE',240));
          DATA1.push(mk('EFRB-CPF-1-023','TK-906B','ALMACENAMIENTO','ESCOTILLA','EMPAQUE',67));
          DATA2.push(mk('EFRB-CPF-2-016','300-TK-0201','PROCESOS','MANHOLE','EMPAQUE',1100));
          DATA2.push(mk('EFRB-CPF-2-020','300TK103','PROCESOS','ESCOTILLA','EMPAQUE',270));
          DATACS.push(mk('EFCS-CEN-008','ETK-1161-B SKIM','SKIM TANK','EMPAQUE','EMPAQUE',2400));
          DATOS_PROPIOS=true; CARGA_INTENTADA=true;
          refrescarTodo();}""")
        await pg.wait_for_timeout(900)
        v=await pg.evaluate("""()=>{
          const q=i=>{const e=document.getElementById(i);return e?e.innerText.trim():null};
          const g1=DATA1.reduce((a,d)=>a+d.tasa,0), g2=DATA2.reduce((a,d)=>a+d.tasa,0),
                gcs=DATACS.reduce((a,d)=>a+d.tasa,0);
          return {verdad:{g1,g2,gcs,n1:DATA1.length,n2:DATA2.length,ncs:DATACS.length},
            kpiTotal:q('kpiTotal'), kpiMedSub:q('kpiMedSub'),
            kpiTotPuntos:q('kpiTotPuntos'), kpiTotSub:q('kpiTotSub'),
            reparto:[...document.querySelectorAll('#kpiTotReparto .fcard-row')].map(r=>
              ((r.querySelector('.fr-cab span')||{}).textContent||'').trim().toUpperCase()
              + '|' + ((r.querySelector('.pts')||{}).textContent||'').trim()
              + '|' + ((r.querySelector('.fr-gh')||{}).textContent||'').trim()).join('\\n'),
            kpiCons:q('kpiConsolidado')}}""")
        t=v['verdad']; n=lambda x:f"{x:,.0f}".replace(',','.')
        print(f"datos: CPF-1 {n(t['g1'])} g/Hr ({t['n1']})  CPF-2 {n(t['g2'])} ({t['n2']})  "
              f"Caño Sur {n(t['gcs'])} ({t['ncs']})")
        print(f"       Rubiales {n(t['g1']+t['g2'])} ({t['n1']+t['n2']})  "
              f"TODO {n(t['g1']+t['g2']+t['gcs'])} ({t['n1']+t['n2']+t['ncs']})")
        print()
        pruebas=[
          ('cifra grande = los dos campos', n(t['g1']+t['g2']+t['gcs']) in (v['kpiTotal'] or '')),
          ('subtítulo trae Rubiales',       n(t['g1']+t['g2']) in (v['kpiMedSub'] or '')),
          ('subtítulo trae Caño Sur',       n(t['gcs']) in (v['kpiMedSub'] or '')),
          ('Total: cuenta todos los puntos', (v['kpiTotPuntos'] or '')==str(t['n1']+t['n2']+t['ncs'])),
          ('Total: suma los dos campos',    n(t['g1']+t['g2']+t['gcs']) in (v['kpiTotSub'] or '')),
          # Las tarjetas sueltas de facilidad se retiraron; sus cifras viven en el
          # reparto de la tarjeta Total, y es ahí donde se comprueban.
          ('CPF-1 en el reparto',           any(l.startswith('CPF-1|') and n(t['g1']) in l
                                                and l.split('|')[1].startswith(str(t['n1']))
                                                for l in (v['reparto'] or '').split(chr(10)))),
          ('CPF-2 en el reparto',           any(l.startswith('CPF-2|') and n(t['g2']) in l
                                                and l.split('|')[1].startswith(str(t['n2']))
                                                for l in (v['reparto'] or '').split(chr(10)))),
          ('Total: lleva su CO2eq',        'ton CO₂eq/año' in (v['kpiTotSub'] or '')),
          ('encabezado sin línea de Rubiales', not (v['kpiCons'] or '').strip()),
        ]
        for nom,ok in pruebas: print(f"  {'OK ' if ok else '>>> MAL'} {nom}")
        print()
        for k in ['kpiTotal','kpiMedSub','kpiTotSub','reparto','kpiCons']:
            print(f'  {k:13}: {v[k]}')
        print('errores:',errs[:3] or 'ninguno')
        await nav.close()
asyncio.run(main())
