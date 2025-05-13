# A partir del archivo de metadatos consolidado (x3 universidades) genera la nueva versión adicionando la etiqueta del tipo de categoría a la que pertenece el tfg
# Genera como resultado la estructura modificada del csv que contiene los metadatos
# Universidad;Tipo Titulacion;Facultad;titulacion;Título;Autor;Año;URL;Archivo Abstract;Palabras Clave;Idioma Abstract;Categoria
# Se adiciona la columna "Categoría"
# Categoría es una agrupación de 10 tipos de titualizaciones en las que se agrupan el total de titulaciones extraídas desde los repositorios y contenidas en el archivo de metadatos original
# Con esta clasificación por categoría se realizarán los análisis posteriores relacionados con ODS y género.
#

import pandas as pd
import unicodedata

# Cargar el archivo CSV (reemplaza el separador si fuera necesario)
df = pd.read_csv("Consol_depur_tfg.csv", sep=";")

# Normalizar los textos de la columna 'titulacion'
df['titulacion_normalizada'] = df['titulacion'].apply(
    lambda x: unicodedata.normalize('NFKD', str(x).lower()).encode('ascii', 'ignore').decode('utf-8')
)

# Definir las categorías y palabras clave
categorias = {
    "Enfermería": ["enfermeria"],
    "Derecho": ["derecho"],
    "Ciencias Sociales": ["psicologia", "sociologia", "filosofia", "antropologia"],
    "Ingenierías": ["ingenieria"],
    "Deporte": ["ciencias de la actividad fisica y del deporte"],
    "Economía y Empresa": ["economia", "comercio", "de empresas", "finanzas", "administrac", "marketing"],
    "Ciencias Exactas": ["en matematicas", "en fisica"],
    "Filologías": ["filologia", "lengua", "literatura", "idioma"],
    "Ciencias Naturales": ["biologia", "ambientales", "rural", "medio", "agricola", "agro", "agraria"],
    "Geografía e Historia": ["en geografia", "en historia"]
}

# Palabras excluidas para Ingeniería
exclusiones_ingenieria = ["rural", "medio", "agricola", "agro", "agraria"]

# Función para asignar categoría
def asignar_categoria(titulacion):
    for categoria, palabras_clave in categorias.items():
        if categoria == "Ingenierías":
            if any(pal in titulacion for pal in palabras_clave) and not any(exc in titulacion for exc in exclusiones_ingenieria):
                return categoria
        else:
            if any(pal in titulacion for pal in palabras_clave):
                return categoria
    return "Otras"

# Aplicar función
df["Categoria"] = df["titulacion_normalizada"].apply(asignar_categoria)

# Guardar el resultado etiquetado
df.drop(columns=["titulacion_normalizada"], inplace=True)
df.to_csv("Consol_depur_tfg_etiquetado.csv", index=False, sep=";")

print("✅ Archivo etiquetado guardado como 'Consol_depur_tfg_etiquetado.csv'")
