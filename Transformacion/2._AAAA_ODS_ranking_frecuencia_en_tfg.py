#
# Lee el archivo CSV 1.1_ENFE_resultados_analisis_ods_en_tfg_nvo_prompt.csv con los resultados de ODS asignados por TFG de la categoría específica.  Con estos datos, 
# genera dos gráficas:
#    Gráfica: Número de TFG diferentes en los que aparece cada ODS al menos una vez (sin duplicar por archivo).

import pandas as pd
import ast
from collections import Counter
import matplotlib.pyplot as plt
from pathlib import Path

# === Configuración ===
archivo_entrada = "1.1_ENFE_resultados_analisis_ods_en_tfg_2ods.csv"
carpeta_salida = Path("ODS_ranking_frecuencia_resultados")
carpeta_salida.mkdir(parents=True, exist_ok=True)

# === Leer archivo CSV ===
df = pd.read_csv(archivo_entrada)

# === Función para limpiar y convertir cadena a lista real ===
def procesar_ods(cadena_ods):
    try:
        lista_ods = ast.literal_eval(cadena_ods)
        return [ods.strip("* ") for ods in lista_ods if isinstance(ods, str)]
    except:
        return []

# === Aplicar limpieza y expansión de ODS por fila ===
df["ods_limpios"] = df["ods_detectados"].apply(procesar_ods)

# === Contar ocurrencias totales de cada ODS ===
todos_ods = sum(df["ods_limpios"], [])  # lista extendida
conteo_ods = Counter(todos_ods)

# === Guardar CSV con el ranking de ODS ===
df_conteo = pd.DataFrame(conteo_ods.items(), columns=["ODS", "Cantidad"]).sort_values(by="Cantidad", ascending=False)
df_conteo.to_csv(carpeta_salida / "2.2_ENFE_ODS_ranking_frecuencia_en_tfg.csv", index=False, encoding="utf-8")

# === Generar gráfico de barras ===
plt.figure(figsize=(12, 6))
plt.barh(df_conteo["ODS"], df_conteo["Cantidad"], color="darkcyan")
plt.xlabel("Número de Trabajos")
plt.title("ODS más abordados en los TFG")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(carpeta_salida / "2.1_ENFE_ODS_ranking_frecuencia_en_tfg.png", dpi=300)
plt.close()

print("✅ Análisis de ODS completado. Resultados en:", carpeta_salida)
