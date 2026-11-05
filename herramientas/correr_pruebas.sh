#!/bin/bash
# Corre las pruebas y dice la verdad sobre cada una.
#
# La versión anterior hacía «python3 x.py | tail -14» y leía $? — que es el de
# tail, no el de Python. Una prueba que reventaba (puerto ocupado, error de
# sintaxis) salía con «[salida 0]» y se leía como verde. Ahora se guarda la
# salida real con PIPESTATUS y además se busca «Traceback», que es lo que
# aparece cuando ni siquiera llegó a arrancar.
cd /tmp/claude-0/-home-claude/5b33160a-cf93-521f-8145-3b092b899fec/scratchpad
rojas=0
for p in "$@"; do
  echo "#### $p"
  salida=$(timeout 240 python3 "$p" 2>&1)
  cod=$?
  echo "$salida" | tail -14
  if [ "$cod" -ne 0 ]; then
    echo "   >>> REVENTÓ (código $cod)"; rojas=$((rojas+1))
  elif echo "$salida" | grep -q "Traceback"; then
    echo "   >>> REVENTÓ (traceback)"; rojas=$((rojas+1))
  else
    echo "   [ok]"
  fi
done
echo
echo "=== pruebas que reventaron: $rojas ==="
