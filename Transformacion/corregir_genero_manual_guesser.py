# Lee archivo [nombres_corregidos.txt] que contiene la lista de nombres no indentificados por gender-guesser
# Lee el archivo [P*_metadatos_genero_guesser.csv] 
# Cruza los 2 archivos anteriores y actualiza los nombres no clasificados de los metadatos con la versión de los nombres corregidos 
# Genera la versión actualizada de [P*_metadatos_genero_guesser.csv] conservando el mismo nombre de archivo original

import pandas as pd
import glob
import os

# Leer archivo de correcciones
with open("nombres_corregidos.txt", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]
nombres_dict = {lines[i]: lines[i + 1] for i in range(0, len(lines), 2)}

print(f"📄 Nombres cargados para corrección: {len(nombres_dict)}")

# Buscar archivos en la carpeta actual
archivos = glob.glob("P*_metadatos_genero_guesser.csv")
total_correcciones = 0

for archivo in archivos:
    df = pd.read_csv(archivo, sep=";")
    cambios = 0

    for nombre, genero_corregido in nombres_dict.items():
        mask = (
            (df["Nombre evaluado"].str.lower() == nombre.lower()) &
            (df["Género inferido"].isin(["desconocido", "androgino"]))
        )
        if mask.any():
            df.loc[mask, "Género inferido"] = genero_corregido
            df.loc[mask, "Fuente de género"] = "manual"
            cambios += mask.sum()

    if cambios > 0:
        df.to_csv(archivo, sep=";", index=False)
        print(f"✅ {cambios} correcciones aplicadas en: {os.path.basename(archivo)}")
        total_correcciones += cambios
    else:
        print(f"➖ Sin cambios en: {os.path.basename(archivo)}")

print(f"🎯 Total correcciones realizadas: {total_correcciones}")
