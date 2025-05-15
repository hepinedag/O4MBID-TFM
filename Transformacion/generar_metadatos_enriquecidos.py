import pandas as pd
import glob
import ast
from collections import defaultdict

# Buscar todos los archivos Px
archivos = sorted(glob.glob("P*_*.csv"))

# Agrupar por prefijo Px
grupos = defaultdict(list)
for archivo in archivos:
    clave = archivo.split("_")[0]  # ej: P1, P2, ...
    grupos[clave].append(archivo)

# Procesar cada grupo
for px, files in grupos.items():
    if len(files) != 2:
        print(f"⚠️  El grupo {px} no tiene exactamente 2 archivos. Se omite.")
        continue

    archivo_ods = next((f for f in files if "_1.1_" in f), None)
    archivo_meta = next((f for f in files if f != archivo_ods), None)

    if not archivo_ods or not archivo_meta:
        print(f"❌ No se pudo identificar correctamente la pareja en {px}")
        continue

    # Cargar los datos
    df_ods = pd.read_csv(archivo_ods)
    df_meta = pd.read_csv(archivo_meta, sep=";")

    # Emparejar por nombre del archivo
    matches = []
    for _, row_ods in df_ods.iterrows():
        archivo_txt = row_ods['archivo'].strip()
        posibles = df_meta[df_meta['Archivo Abstract'].str.contains(archivo_txt, na=False, regex=False)]
        if not posibles.empty:
            for _, row_meta in posibles.iterrows():
                try:
                    ods_list = ast.literal_eval(row_ods['ods_detectados'])
                    ods_1 = ods_list[0].replace("**", "").strip() if len(ods_list) > 0 else ""
                    ods_2 = ods_list[1].replace("**", "").strip() if len(ods_list) > 1 else ""
                except:
                    ods_1, ods_2 = "", ""

                fila = row_meta.to_dict()
                fila["ODS 1"] = ods_1
                fila["ODS 2"] = ods_2
                matches.append(fila)

    if not matches:
        print(f"⚠️  No se pudo emparejar ningún registro en {px}.")
        continue

    df_resultado = pd.DataFrame(matches)

    # Guardar archivo enriquecido
    nombre_salida = f"{px}_metadatos_enriquecido.csv"
    df_resultado.to_csv(nombre_salida, sep=";", index=False)
    print(f"✅ Archivo enriquecido generado: {nombre_salida}")
