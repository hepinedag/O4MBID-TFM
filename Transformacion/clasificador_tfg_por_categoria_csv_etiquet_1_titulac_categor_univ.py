import pandas as pd
import os
import shutil
from pathlib import Path
import unicodedata

# === CONFIGURACIÓN ===
CSV_ETIQUETADO = "Consol_depur_tfg_etiquetado.csv"
RUTA_ABSTRACTS = "./Archivos_tfg_todas_univsdds"
RUTA_SALIDA = "./salida_categorias_tfg"

# === CARGA DEL CSV ETIQUETADO ===
df = pd.read_csv(CSV_ETIQUETADO, sep=";")

# === Verificar y crear 'titulacion_normalizada' si no existe ===
if 'titulacion_normalizada' not in df.columns:
    df['titulacion_normalizada'] = df['titulacion'].apply(
        lambda x: unicodedata.normalize('NFKD', str(x).lower()).encode('ascii', 'ignore').decode('utf-8')
    )

# === CREAR DIRECTORIO DE SALIDA PRINCIPAL ===
Path(RUTA_SALIDA).mkdir(exist_ok=True)

# === LISTA DE CATEGORÍAS A PROCESAR ===
categorias = [
    "Enfermería",
    "Derecho",
    "Ciencias Sociales",
    "Ingenierías",
    "Deporte",
    "Economía y Empresa",
    "Ciencias Exactas",
    "Filologías",
    "Ciencias Naturales",
    "Geografía e Historia"
]

# === PROCESO DE CLASIFICACIÓN ===
for categoria in categorias:
    df_cat = df[df["Categoria"] == categoria]

    if df_cat.empty:
        print(f"⚠️  No se encontraron registros para la categoría: {categoria}")
        continue

    # Crear carpeta de salida para la categoría
    carpeta_categoria = Path(RUTA_SALIDA) / categoria.replace(" ", "_")
    carpeta_categoria.mkdir(parents=True, exist_ok=True)

    # Guardar CSV de metadatos completo (con columnas adicionales)
    ruta_csv = carpeta_categoria / f"metadatos_{categoria.replace(' ', '_')}.csv"
    df_cat.to_csv(ruta_csv, index=False, sep=";")

    # Copiar los abstracts
    for archivo in df_cat["Archivo Abstract"]:
        nombre_archivo = os.path.basename(str(archivo)).strip()
        ruta_origen = os.path.join(RUTA_ABSTRACTS, nombre_archivo)
        ruta_destino = carpeta_categoria / nombre_archivo

        if os.path.exists(ruta_origen):
            shutil.copy(ruta_origen, ruta_destino)
        else:
            print(f"⚠️  Abstract no encontrado: {ruta_origen}")

print("✅ Clasificación y generación de metadatos finalizada. Archivos generados con columnas completas.")

# === RESUMEN DE TITULACIONES INCLUIDAS POR CATEGORÍA CON UNIVERSIDADES ===
print("\n📌 Titulaciones agrupadas por categoría (con universidades):\n")

resumen = []

for categoria in categorias:
    df_cat = df[df["Categoria"] == categoria]
    if not df_cat.empty:
        print(f"🗂️  {categoria}:")
        agrupado = df_cat.groupby("titulacion")["Universidad"].unique()
        resumen_categoria = []
        for tit, univs in agrupado.items():
            universidades = ", ".join(sorted(univs))
            print(f"   - {tit} ({universidades})")
            resumen_categoria.append(f"{tit} ({universidades})")
        print()
        resumen.append({"Categoria": categoria, "Titulaciones": resumen_categoria})

# === Guardar el resumen en archivo ===
with open("resumen_titulaciones_por_categoria.txt", "w", encoding="utf-8") as f:
    for item in resumen:
        f.write(f"{item['Categoria']}:\n")
        for tit in item['Titulaciones']:
            f.write(f"  - {tit}\n")
        f.write("\n")

print("✅ Resumen guardado en 'resumen_titulaciones_por_categoria.txt'")
