# Herramientas del GOP-F-007

Cómo se hizo el molde que el tablero usa para las fichas de cierre, y cómo
comprobar que un libro generado abre de verdad en Excel.

    molde.py       saca de un GOP-F-007 lleno una ficha en blanco (30 KB)
    fichas.py      arma un libro con una ficha por cierre — la misma cirugía
                   que hace el tablero, escrita aquí para poder probarla
    regenerar.py   rehace molde y ejemplo, y los revisa

La comprobación mira tres cosas que Excel valida y los visores no:

  - que la pestaña activa exista (un `activeTab` que apunte más allá de la
    última hoja hace que Excel se niegue a abrir el archivo);
  - que `docProps/app.xml` liste exactamente las hojas que tiene el libro;
  - que cada pieza XML sea XML bien formado, con su etiqueta raíz.

Las tres salieron de errores reales: el archivo abría bien en LibreOffice y
Excel pedía recuperarlo.
