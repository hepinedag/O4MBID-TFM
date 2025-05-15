# analisis_final_genero_ods.py (completo con todas las gráficas y correcciones aplicadas)

import pandas as pd
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import os

sns.set(style="whitegrid")

output_dir = "salidas_ods_genero"
os.makedirs(output_dir, exist_ok=True)

px_nombres = {
    "P1": "Ciencias Sociales",
    "P2": "Deportes",
    "P3": "Ciencias Naturales",
    "P4": "Derecho",
    "P5": "Economía y Empresas",
    "P6": "Enfermeria",
    "P7": "Filologías",
    "P8": "Geografía e Historia",
    "P9": "Ingenierias"
}

consolidado_ods = defaultdict(lambda: defaultdict(int))
consolidado_genero_total = defaultdict(int)
consolidado_genero_anio = defaultdict(lambda: defaultdict(int))
consolidado_ods_anio = defaultdict(lambda: defaultdict(int))
nombres_clasificados = []

archivos = sorted(glob.glob("P*_metadatos_genero_guesser.csv"))

# Función para agregar ratios selectivos
def agregar_ratios_selectivos(ax, df_data):
    ratios_data = []
    for idx, row in df_data.iterrows():
        total = row.sum()
        if total == 0:
            continue
        acumulado = 0
        row_sorted = row.sort_values(ascending=False)
        contador = 0
        for ods, valor in row_sorted.items():
            if valor == 0:
                continue
            porcentaje = (valor / total) * 100
            x = df_data.index.get_loc(idx)
            y = df_data.loc[idx][:ods].sum() - valor / 2

            # Solo etiquetas a los 4 más grandes o acumulando 80%
            if contador < 4 or acumulado / total < 0.8:
                ax.text(x, y, f"{valor} ({porcentaje:.1f}%)", ha='center', fontsize=6)
                contador += 1
                acumulado += valor

            ratios_data.append({
                'Año': idx,
                'ODS': ods,
                'Cantidad': valor,
                'Total año': total,
                'Ratio (%)': round(porcentaje, 1)
            })
    return ratios_data

for archivo in archivos:
    df = pd.read_csv(archivo, sep=";")
    px = archivo.split("_")[0]
    nombre_categoria = px_nombres.get(px, px)

    ods_anio = defaultdict(lambda: defaultdict(int))
    total_ods_counter = Counter()
    resumen_total_genero = defaultdict(int)
    resumen_genero_anio = defaultdict(lambda: defaultdict(int))
    resumen = defaultdict(lambda: defaultdict(int))

    for _, row in df.iterrows():
        nombre = row["Nombre evaluado"]
        genero = row["Género inferido"]
        anio = str(row["Año"]).strip() if not pd.isna(row["Año"]) else "desconocido"
        resumen_total_genero[genero] += 1
        consolidado_genero_total[genero] += 1
        resumen_genero_anio[anio][genero] += 1
        consolidado_genero_anio[anio][genero] += 1

        for col in ["ODS 1", "ODS 2"]:
            if pd.notna(row[col]):
                ods = row[col].strip()
                resumen[ods][genero] += 1
                consolidado_ods[ods][genero] += 1
                ods_anio[ods][anio] += 1
                consolidado_ods_anio[ods][anio] += 1
                total_ods_counter[ods] += 1

        nombres_clasificados.append((nombre, genero, row["Fuente de género"]))

    # Tabla y gráfico de género vs ODS
    df_resumen = pd.DataFrame(resumen).T.fillna(0).astype(int)
    df_resumen.to_csv(f"{output_dir}/{px}_genero_vs_ods.csv", sep=";")
    ax = df_resumen.plot(kind="bar", stacked=True, figsize=(14, 7), colormap="Set2")
    plt.title(f"{nombre_categoria} - Género vs ODS")
    for container in ax.containers:
        labels = [int(v.get_height()) if v.get_height() > 0 else '' for v in container]
        ax.bar_label(container, labels=labels, label_type='center', fontsize=7)
    plt.xlabel("ODS")
    plt.ylabel("TFG")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{px}_genero_vs_ods.png", dpi=300)
    plt.close()

    # TFG por género
    df_total = pd.Series(resumen_total_genero)
    df_ratio = round((df_total / df_total.sum()) * 100, 1)
    ax = df_total.plot(kind="bar", figsize=(8, 5), color="skyblue")
    for i, v in enumerate(df_total):
        ax.text(i, v + 0.5, f"{v} ({df_ratio[i]}%)", ha="center")
    plt.title(f"{nombre_categoria} - TFG por Género (con ratio)")
    plt.ylabel("TFG")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{px}_genero_total_ratio.png", dpi=300)
    plt.close()

    # TFG por año y género
    df_anio = pd.DataFrame(resumen_genero_anio).T.fillna(0).astype(int)
    df_anio.sort_index(inplace=True)
    ax = df_anio.plot(kind="bar", stacked=True, figsize=(14, 6), colormap="coolwarm")
    plt.title(f"{nombre_categoria} - TFG por Género y Año (con ratio)")
    plt.xlabel("Año")
    plt.ylabel("TFG")
    for container in ax.containers:
        labels = [int(bar.get_height()) if bar.get_height() > 0 else '' for bar in container]
        ax.bar_label(container, labels=labels, label_type='center', fontsize=7)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{px}_genero_por_anio.png", dpi=300)
    plt.close()

    # ODS detectados por año
    # Transformar a DataFrame
    df_ods_anio = pd.DataFrame(ods_anio).fillna(0).astype(int)
    df_ods_anio = df_ods_anio.sort_index()

    # Graficar
    # plt.figure(figsize=(16, 8))  # Creamos la figura global
    # ax = df_ods_anio.plot(kind="bar", stacked=True, colormap="tab20")
    # Creamos figura y ejes explícitos
    fig, ax = plt.subplots(figsize=(16, 8))

    # Graficamos PASANDO el eje explícitamente
    df_ods_anio.plot(kind="bar", stacked=True, colormap="tab20", ax=ax)

    # Formato
    plt.title(f"{nombre_categoria} - ODS detectados por Año")
    plt.xlabel("Año")
    plt.ylabel("TFG por ODS")
    plt.xticks(rotation=45, ha="right")

    # Leyenda (fuera pero visible)
    plt.legend(title="ODS", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")

    # Agregar ratios selectivos
    ratios_info = agregar_ratios_selectivos(ax, df_ods_anio)

    # Guardar trazabilidad de ratios
    df_ratios = pd.DataFrame(ratios_info)
    df_ratios.to_csv(f"{output_dir}/{px}_trazabilidad_ratios.csv", sep=";", index=False)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/{px}_ods_por_anio_ratio.png", dpi=300)
    plt.close()
    
    # ODS más abordados
    total_sum = sum(total_ods_counter.values())
    df_top_ods = pd.Series(total_ods_counter).sort_values(ascending=True)
    df_top_ratio = round((df_top_ods / total_sum) * 100, 1)
    ax = df_top_ods.plot(kind="barh", figsize=(10, 8), color="lightgreen")
    for i, v in enumerate(df_top_ods):
        ax.text(v + 1, i, f"{v} ({df_top_ratio[i]}%)", va="center")
    plt.title(f"{nombre_categoria} - ODS más abordados (con ratio vertical)")
    plt.xlabel("TFG")
    plt.ylabel("ODS")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{px}_ods_mas_abordados.png", dpi=300)
    plt.close()

# Consolidado: Género vs ODS
consol_genero_ods = pd.DataFrame(consolidado_ods).T.fillna(0).astype(int)
ax = consol_genero_ods.plot(kind="bar", stacked=True, figsize=(16, 8), colormap="tab10")
plt.title("Consolidado - Género vs ODS (Todas las categorías)")
plt.xlabel("ODS")
plt.ylabel("TFG")
for container in ax.containers:
    labels = [int(v.get_height()) if v.get_height() > 0 else '' for v in container]
    ax.bar_label(container, labels=labels, label_type='center', fontsize=7)
plt.tight_layout()
plt.savefig(f"{output_dir}/Consolidado_genero_vs_ods.png", dpi=300)
plt.close()
consol_genero_ods.to_csv(f"{output_dir}/Consolidado_genero_vs_ods.csv", sep=";")

# Consolidado: Total por género
consol_genero_total = pd.Series(consolidado_genero_total)
consol_ratio = round((consol_genero_total / consol_genero_total.sum()) * 100, 1)
ax = consol_genero_total.plot(kind="bar", figsize=(8, 5), color="orange")
for i, v in enumerate(consol_genero_total):
    ax.text(i, v + 0.5, f"{v} ({consol_ratio[i]}%)", ha="center")
plt.title("Consolidado - TFG por Género (con ratio) (Todas las categorías)")
plt.ylabel("TFG")
plt.tight_layout()
plt.savefig(f"{output_dir}/Consolidado_genero_total_ratio.png", dpi=300)
plt.close()

# Consolidado: TFG por año y género
consol_anio = pd.DataFrame(consolidado_genero_anio).T.fillna(0).astype(int)
consol_anio.sort_index(inplace=True)
ax = consol_anio.plot(kind="bar", stacked=True, figsize=(14, 6), colormap="Set1")
plt.title("Consolidado - TFG por Género y Año (Todas las categorías)")
plt.xlabel("Año")
plt.ylabel("TFG")
for container in ax.containers:
    labels = [int(v.get_height()) if v.get_height() > 0 else '' for v in container]
    ax.bar_label(container, labels=labels, label_type='center', fontsize=7)
plt.tight_layout()
plt.savefig(f"{output_dir}/Consolidado_genero_por_anio.png", dpi=300)
plt.close()

# Consolidado: ODS detectados por año (CORREGIDO - versión completa)
df_consol_ods_anio = pd.DataFrame(consolidado_ods_anio).fillna(0).astype(int)  # Crear DataFrame a partir de consolidado_ods_anio
df_consol_ods_anio = df_consol_ods_anio.sort_index()  # Ordenar por año (índice)

# Crear figura y ejes explícitos
fig, ax = plt.subplots(figsize=(16, 7))

# Graficar PASANDO el eje explícitamente
df_consol_ods_anio.plot(kind="bar", stacked=True, colormap="tab20", ax=ax)  # O usar colormap="tab20" como antes

# Formato de la gráfica
plt.title("Consolidado - ODS detectados por Año")
plt.xlabel("Año")
plt.ylabel("TFG por ODS")
plt.xticks(rotation=45, ha="right")  # Rotar etiquetas del eje X

# Leyenda
plt.legend(title="ODS", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")  # Posicionar leyenda

# Agregar ratios selectivos
ratios_info = agregar_ratios_selectivos(ax, df_consol_ods_anio)

# Guardar trazabilidad de ratios
df_ratios = pd.DataFrame(ratios_info)
df_ratios.to_csv(f"{output_dir}/Consolidado_trazab_ratios_ods_año.csv", sep=";", index=False)

# Guardar la gráfica
plt.tight_layout()
plt.savefig(f"{output_dir}/Consolidado_ods_por_anio_ratio.png", dpi=300)
plt.close()

# Consolidado: ODS más abordados
df_consol_ods_anio_tmp = pd.DataFrame(consolidado_ods_anio).fillna(0).astype(int).T  # Crear DataFrame a partir de consolidado_ods_anio
df_consol_ods_anio_tmp = df_consol_ods_anio_tmp.sort_index()  # Ordenar por año (índice)
consol_total_ods = df_consol_ods_anio_tmp.sum(axis=1).sort_values(ascending=True)
consol_sum = consol_total_ods.sum()
df_ratio_consol = round((consol_total_ods / consol_sum) * 100, 1)
ax = consol_total_ods.plot(kind="barh", figsize=(10, 8), color="orchid")
consol_total_ods.plot(kind="barh", figsize=(10, 8), color="orchid")
for i, v in enumerate(consol_total_ods):
    ax.text(v + 1, i, f"{v} ({df_ratio_consol[i]}%)", va="center")
plt.title("Consolidado - ODS más abordados (Todas las categorías)")
plt.xlabel("TFG")
plt.ylabel("ODS")
plt.tight_layout()
plt.savefig(f"{output_dir}/Consolidado_ods_mas_abordados.png", dpi=300)
plt.close()

# Guardar nombres clasificados
df_nombres = pd.DataFrame(nombres_clasificados, columns=["Nombre evaluado", "Género inferido", "Fuente de género"])
df_nombres["Frecuencia"] = df_nombres.groupby("Nombre evaluado")["Nombre evaluado"].transform("count")
df_nombres = df_nombres.drop_duplicates()
df_nombres.to_csv(f"{output_dir}/Consolidado_nombres_genero.csv", sep=";", index=False)
