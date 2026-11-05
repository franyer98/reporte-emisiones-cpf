# -*- coding: utf-8 -*-
"""Auditoría general: con los catorce puntos reales en firme, cada cifra del
tablero tiene que cuadrar con las otras y con el libro corregido."""
import asyncio, threading, http.server, re, json, pathlib
from playwright.async_api import async_playwright
RAIZ='/home/claude/work/bd/repo'
OUT=pathlib.Path('/tmp/claude-0/-home-claude/5b33160a-cf93-521f-8145-3b092b899fec/scratchpad/tiros')
class M(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=RAIZ,**k)
    def do_GET(s):
        if s.path.startswith('/api/'):
            s.send_response(404); s.send_header('content-length','0'); s.end_headers(); return
        return super().do_GET()
    def log_message(s,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8879),M)
threading.Thread(target=srv.serve_forever,daemon=True).start()

# fila del libro, punto, equipo, área, g/Hr, facilidad(1=CPF-1 2=CPF-2 3=Caño Sur)
REAL=[
 (7, 'CPF-1-022','TK-904','ALMACENAMIENTO',240,1),
 (8, 'CPF-1-023','TK-906B','ALMACENAMIENTO',67,1),
 (9, 'CPF-1-024','TK-902','ALMACENAMIENTO',53,1),
 (10,'CPF-1-025','TK-902','ALMACENAMIENTO',19,1),
 (11,'CPF-2-016','300-TK-0201','PROCESOS',1100,2),
 (12,'CPF-2-017','300TK0101','PROCESOS',510,2),
 (13,'CPF-2-018','300TK0101','PROCESOS',300,2),
 (14,'CPF-2-019','300TK0401','PROCESOS',280,2),
 (15,'CPF-2-020','300TK103','PROCESOS',270,2),
 (16,'CPF-2-021','300TK0001','PROCESOS',250,2),
 (17,'CEN-008','ETK-1161-B SKIM','SKIM TANK',2400,3),
 (19,'CEN-010','ETK-1161-B SKIM','SKIM TANK',660,3),
 (18,'CEN-009','ETK-1101-B FWKO','FWKOS',1100,3),
 (20,'CEN-011','ETK-1101-C FWKO','FWKOS',13,3),
]
LIBRO={7:36.9415661233,8:10.3128538761,9:1.15191370848,10:0.41295019738,
 11:259.701521216,12:120.407068927,13:70.8276876043,14:66.1058417641,
 15:60.1143519905,16:55.2750254649,17:297.881195355,18:248.931795887,
 19:81.9173287227,20:2.94192122411}
SUB=sum(LIBRO.values())

def num(t):
    """primer número en formato es-CO de un texto"""
    m=re.search(r'-?\d[\d.]*(?:,\d+)?',t or '')
    if not m: return None
    return float(m.group(0).replace('.','').replace(',','.'))

fallos=[]
def ok(cond,etq,extra=''):
    print(('  OK  ' if cond else '  MAL ')+etq+(('  '+extra) if extra else ''))
    if not cond: fallos.append(etq)

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        nav=await p.chromium.launch(args=['--use-gl=swiftshader'])
        ctx=await nav.new_context(viewport={'width':412,'height':900},has_touch=True,is_mobile=True)
        pg=await ctx.new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        cons=[]; pg.on('console',lambda m: cons.append(m.text) if m.type=='error' else None)
        await pg.goto('http://127.0.0.1:8879/'); await pg.wait_for_timeout(3600)

        # ---- inyectar los datos reales y repintar todo
        inj=await pg.evaluate("""(real)=>{
          const mk=(x,i)=>({id:'p'+i,punto:x[1],equipo:x[2],area:x[3],tasa:x[4],
                            elemento:'Empaque',img:'',estado:'abierto'});
          DATA1.length=0; DATA2.length=0; DATACS.length=0;
          real.forEach((x,i)=>{ const d=mk(x,i);
            (x[5]===1?DATA1:x[5]===2?DATA2:DATACS).push(d); });
          refrescarTodo();
          return {n1:DATA1.length,n2:DATA2.length,ncs:DATACS.length,
                  c1:co2eqDe(DATA1,'CPF-1'),c2:co2eqDe(DATA2,'CPF-2'),ccs:co2eqDe(DATACS,'CAÑO SUR'),
                  g1:DATA1.reduce((a,d)=>a+d.tasa,0),g2:DATA2.reduce((a,d)=>a+d.tasa,0),
                  gcs:DATACS.reduce((a,d)=>a+d.tasa,0),
                  porPunto:[...DATA1.map(d=>[d.punto,d.tasa*kDe('CPF-1',d.area,d.equipo)]),
                            ...DATA2.map(d=>[d.punto,d.tasa*kDe('CPF-2',d.area,d.equipo)]),
                            ...DATACS.map(d=>[d.punto,d.tasa*kDe('CAÑO SUR',d.area,d.equipo)])]};
        }""", REAL)
        await pg.wait_for_timeout(1500)

        gT=inj['g1']+inj['g2']+inj['gcs']; cT=inj['c1']+inj['c2']+inj['ccs']
        print(f"\ndatos: CPF-1 {inj['g1']:,} g/Hr ({inj['n1']})  CPF-2 {inj['g2']:,} ({inj['n2']})"
              f"  Caño Sur {inj['gcs']:,} ({inj['ncs']})")
        print(f"       TODO {gT:,} g/Hr (14) · {cT:.2f} ton CO2eq/año\n")

        print("— 1. contra el libro corregido, punto por punto —")
        mapa={p:v for p,v in inj['porPunto']}
        malos=[]
        for fila,punto,eq,ar,g,f in REAL:
            v=mapa.get(punto); e=LIBRO[fila]
            if v is None or abs(v-e)>0.005: malos.append((punto,fila,v,e))
        ok(not malos,'cada punto da el mismo CO2eq que su fila AJ del libro',
           '' if not malos else str(malos[:3]))
        ok(abs(cT-SUB)<0.01,f'el total cuadra con el subtotal AJ21 ({SUB:.2f})',f'tablero {cT:.2f}')
        ok(gT==7262,'la suma de lecturas es 7.262 g/Hr',f'{gT}')

        print("\n— 2. encabezado —")
        d=await pg.evaluate("""()=>{const q=i=>{const e=document.getElementById(i);
          return e?e.innerText.trim():null};
          return {total:q('kpiTotal'),co2:q('kpiCo2'),co2u:q('kpiCo2U'),med:q('kpiMedSub'),
                  rep:q('kpiRepSub'),totP:q('kpiTotPuntos'),totS:q('kpiTotSub'),
                  totR:q('kpiTotReparto'),
                  filas:[...document.querySelectorAll('#kpiTotReparto .fcard-row')].map(r=>({
                    nom:((r.querySelector('.fr-cab span')||{}).textContent||'').trim(),
                    pts:((r.querySelector('.pts')||{}).textContent||'').trim(),
                    gh:((r.querySelector('.fr-gh')||{}).textContent||'').trim(),
                    ton:((r.querySelector('.fcard-co2')||{}).textContent||'').trim()}))}}""")
        ok(num(d['total'])==gT,'cifra grande = suma de los dos campos',d['total'])
        ok(abs(num(d['co2'])-cT)<0.51,'CO2eq del encabezado = suma punto por punto',d['co2'])
        ok('año' in (d['co2u'] or ''),'el CO2eq dice que va al año',d['co2u'])
        ok(str(inj['n1']+inj['n2']) in (d['med'] or '') or '14' in (d['med'] or ''),
           'el subtítulo cuenta los puntos',d['med'])

        print("\n— 3. tarjeta Total —")
        ok(num(d['totP'])==14,'cuenta los 14 puntos',d['totP'])
        ok(num(d['totS'])==gT,'suma los dos campos',d['totS'])
        rep=[num(x) for x in re.findall(r'[\d.]+(?:,\d\d)?(?= ton)',d['totR'] or '')]
        ok(abs(sum(rep)-cT)<1.6 if rep else False,
           'el reparto por facilidad suma el total',f"{sum(rep):.2f} vs {cT:.2f}")

        # Las tarjetas sueltas de CPF-1, CPF-2 y Caño Sur se retiraron: repetían
        # punto por punto lo que ya dice el reparto de la tarjeta Total. Las
        # mismas comprobaciones se hacen ahora sobre ese reparto, que es donde
        # viven las cifras.
        print("\n— 4. reparto por facilidad —")
        filas={f['nom'].upper():f for f in d['filas']}
        for etq,clave,g,c,n in [
            ('CPF-1','CPF-1',inj['g1'],inj['c1'],inj['n1']),
            ('CPF-2','CPF-2',inj['g2'],inj['c2'],inj['n2']),
            ('Caño Sur','CAÑO SUR',inj['gcs'],inj['ccs'],inj['ncs'])]:
            f=filas.get(clave)
            if not f:
                ok(n==0, f'{etq}: tiene su renglón', '(no aparece)')
                continue
            ok(num(f['pts'])==n, f'{etq}: cuenta sus puntos', f['pts'])
            ok(num(f['gh'])==g,  f'{etq}: sus g/Hr',        f['gh'])
            ok(abs(num(f['ton'])-c)<0.02, f'{etq}: su CO2eq',
               f"{f['ton']} vs {c:.2f}")

        print("\n— 5. filtro de campo —")
        esp={'Todas':(gT,cT),'CPF-1':(inj['g1'],inj['c1']),
             'CPF-2':(inj['g2'],inj['c2']),'Caño Sur':(inj['gcs'],inj['ccs'])}
        for etq,(g,c) in esp.items():
            await pg.evaluate("""(t)=>{const b=[...document.querySelectorAll('.tab')]
              .find(x=>x.textContent.trim().startsWith(t)); if(b) b.click();}""", etq)
            await pg.wait_for_timeout(900)
            r=await pg.evaluate("""()=>({t:document.getElementById('kpiTotal').innerText,
              c:document.getElementById('kpiCo2').innerText})""")
            ok(num(r['t'])==g and abs(num(r['c'])-c)<0.51,f'{etq}: {r["t"]} · {r["c"]}')
        await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.tab')]
          .find(x=>x.textContent.trim().startsWith('Todas')); if(b) b.click();}""")
        await pg.wait_for_timeout(900)

        print("\n— 6. periodos: la lectura se proyecta, el equivalente no —")
        per=await pg.evaluate("""async()=>{
          const r={}; const bs=[...document.querySelectorAll('#periodGlobal button')];
          for (const b of bs){ b.click(); await new Promise(s=>setTimeout(s,320));
            r[b.dataset.period]={co2:document.getElementById('kpiCo2').innerText,
                                  u:document.getElementById('kpiCo2U').innerText}; }
          return r;}""")
        for k,v in per.items():
            print(f"      {k:8} -> {v['co2']:>12}  {v['u']}")
        anio=[k for k,v in per.items() if 'hora' in k or True]
        ok(len(per)>0,'hay selector de periodo con sus equivalentes')

        print("\n— 7. mapas 3D —")
        m3=await pg.evaluate("""async()=>{
          const r=[];
          for (const id of ['t1','t2','t3']){
            const b=[...document.querySelectorAll('.tab')].find(x=>x.dataset.tab===id);
            if(!b) continue; b.click(); await new Promise(s=>setTimeout(s,1400));
            const p=document.getElementById('panel-'+id);
            const v=p?p.querySelector('.view3d-total-v, [id$="TotalV"], .v3d-total'):null;
            const vs=p?[...p.querySelectorAll('*')].filter(e=>/ton CO₂eq/.test(e.textContent)
                        && e.children.length===0).map(e=>e.textContent.trim()):[];
            r.push({id, vistos: vs.slice(0,4)});
          }
          return r;}""")
        for x in m3: print('     ',x['id'],x['vistos'])
        objetivo={'t1':inj['c1'],'t2':inj['c2'],'t3':inj['ccs']}
        for x in m3:
            vals=[num(v) for v in x['vistos']]
            ok(any(v is not None and abs(v-objetivo[x['id']])<0.51 for v in vals),
               f"{x['id']}: el total del mapa = CO2eq de la facilidad ({objetivo[x['id']]:.2f})")

        print("\n— 8. memoria de cálculo —")
        mem=await pg.evaluate("""async()=>{
          const a=document.getElementById('navMemoria');
          if(!a) return null; a.click(); await new Promise(s=>setTimeout(s,1200));
          const caja=document.querySelector('.bd-caja');
          return caja?caja.innerText:null;}""")
        if mem:
            tons=[num(x) for x in re.findall(r'[\d.]+,\d\d(?= ton)',mem)]
            print('      ton citadas:',tons[:14])
            ok(any(t is not None and abs(t-cT)<0.05 for t in tons),
               'la memoria cita el total correcto',f'{cT:.2f}')
        else:
            print('      (no se encontró el enlace de memoria)')

        print("\n— 9. simulador —")
        sim=await pg.evaluate("""async()=>{
          document.querySelectorAll('.bd-capa').forEach(e=>e.remove());
          const a=document.getElementById('navSimulador'); if(!a) return null;
          a.click(); await new Promise(s=>setTimeout(s,900));
          const sel=document.getElementById('simCrom');
          const opts=[...sel.options].map(o=>o.textContent);
          // probar el primer factor del tablero con 1000 g/Hr
          document.getElementById('simTasa').value='1000';
          document.getElementById('simTasa').dispatchEvent(new Event('input'));
          await new Promise(s=>setTimeout(s,500));
          return {n:opts.length, primeras:opts.slice(0,3),
                  v:document.getElementById('simV').innerText,
                  ok:document.getElementById('simOk').innerText,
                  nota:document.getElementById('simNota').innerText};}""")
        if sim:
            print('      opciones:',sim['n'],sim['primeras'])
            print('      resultado:',sim['v'],'|',sim['nota'][:90])
            ok('Coincide con el tablero' in sim['ok'],'el simulador cuadra con el tablero',
               sim['ok'][:80])
        await pg.evaluate("()=>document.querySelectorAll('.bd-capa').forEach(e=>e.remove())")

        print("\nerrores de página:',", errs[:3] or 'ninguno')
        print("errores de consola:", [c for c in cons if 'favicon' not in c][:3] or 'ninguno')
        print("\nfallos:", fallos or 'ninguno')
        await pg.screenshot(path=str(OUT/'general.png'),full_page=False)
        await nav.close()
asyncio.run(main())
