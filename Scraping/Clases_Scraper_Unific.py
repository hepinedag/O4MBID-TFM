class UamScraper:
    def main(self):
        import os
        import time
        import csv
        import re
        import logging
        import random

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger()

        def log_message(msg):
            logger.info(msg)
            print(msg)

        def setup_driver():
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/110.0.5481.77 Safari/537.36")
            chrome_options.add_argument(f"--user-agent={user_agent}")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''}
            )
            return driver

        def random_delay(min_s=2, max_s=5):
            time.sleep(random.uniform(min_s, max_s))

        def obtener_html(driver, url):
            try:
                random_delay()
                driver.get(url)
                random_delay()
                html = driver.page_source
                log_message(f"Página descargada correctamente: {url}")
                return html
            except Exception as e:
                log_message(f"Error al acceder a {url}: {e}")
                return None

        def guardar_abstract(abstract_text, titulo, anio, tipo):
            if tipo == "Máster":
                folder = "abstracts_uam_TFM"
            elif tipo == "Grado":
                folder = "abstracts_uam_TFG"
            else:
                folder = "abstracts_uam_TFM"
            
            os.makedirs(folder, exist_ok=True)
            titulo_safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', titulo)[:30]
            hash_id = abs(hash(titulo)) % (10**8)
            prefijo = "RND_" if not abstract_text.strip() or abstract_text.strip() == "" or abstract_text == "Resumen no disponible" else ""
            filename = f"{prefijo}{titulo_safe}_{anio}_{hash_id}.txt"
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(abstract_text)
                log_message(f"Abstract guardado en {filepath}")
            except Exception as e:
                log_message(f"Error guardando abstract: {e}")
                filepath = ""
            return filepath

        def get_items_from_listing(html):
            base_url = "https://repositorio.uam.es"
            soup = BeautifulSoup(html, 'html.parser')
            items_links = []
            item_divs = soup.find_all("div", class_="row ds-artifact-item")
            for div in item_divs:
                a_tag = div.find("a", href=True)
                if a_tag:
                    href = a_tag["href"]
                    if href.startswith("/"):
                        href = base_url + href
                    items_links.append(href)
            return items_links

        def get_metadata_full(driver, item_url, tipo):
            full_url = item_url + "?show=full"
            html = obtener_html(driver, full_url)
            if not html:
                return None
            soup = BeautifulSoup(html, 'html.parser')
            
            universidad = "Universidad Autónoma de Madrid"
            facultad = ""
            titulacion = ""
            titulo = ""
            autor = ""
            anio = ""
            palabras_clave = ""
            idioma_abstract = ""
            abstract_text = ""
            
            table = soup.find("table", class_=lambda x: x and ("detailtable" in x or "itemDisplayTable" in x))
            if table:
                rows = table.find_all("tr", class_=lambda x: x and "ds-table-row" in x)
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue
                    field = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    if field == "dc.title":
                        titulo = value
                    elif field == "dc.contributor.author":
                        autor = value
                    elif field == "dc.date.issued":
                        anio = value[:4]
                    elif field == "dc.description.abstract":
                        abstract_text = value
                    elif field == "dc.language.iso":
                        idioma_abstract = value
                    elif field == "dc.description":
                        if not titulacion:
                            titulacion = value
                    elif field in ["dc.subject", "dc.subject.other"]:
                        if palabras_clave:
                            palabras_clave += "; " + value
                        else:
                            palabras_clave = value
                    elif field == "dc.publisher":
                        facultad = value
                    elif field == "dc.facultaduam":
                        facultad = value

            if not abstract_text:
                abstract_text = "Resumen no disponible"
            archivo_abstract = guardar_abstract(abstract_text, titulo, anio, tipo)
            
            if not titulacion:
                titulacion = "No disponible"
            
            return {
                "Universidad": universidad,
                "Tipo Titulación": tipo,
                "Facultad": facultad,
                "Titulación": titulacion,
                "Título": titulo if titulo else "Título no disponible",
                "Autor": autor,
                "Año": anio,
                "URL": item_url,
                "Archivo Abstract": archivo_abstract,
                "Palabras Clave": palabras_clave,
                "Idioma Abstract": idioma_abstract
            }

        driver = setup_driver()

        collections = [
            {"filter": "masterThesis", "label": "Máster"},
            {"filter": "bachelorThesis", "label": "Grado"}
        ]
        
        all_item_links = []
        
        for col in collections:
            base_list_url = ("https://repositorio.uam.es/handle/10486/700637/discover?"
                             "rpp=10&etal=0&group_by=none")
            filtro = f"&filtertype_0=type&filter_relational_operator_0=equals&filter_0={col['filter']}"
            page = 1
            while True:
                list_url = f"{base_list_url}&page={page}{filtro}"
                html_listing = obtener_html(driver, list_url)
                if not html_listing:
                    break
                items_links = get_items_from_listing(html_listing)
                if not items_links:
                    log_message(f"No se encontraron ítems en la página {page} para {col['label']}.")
                    break
                for link in items_links:
                    all_item_links.append({"url": link, "tipo": col["label"]})
                log_message(f"[{col['label']}] Página {page} procesada, {len(items_links)} ítems encontrados.")
                page += 1

        log_message(f"Total de ítems a procesar: {len(all_item_links)}")

        output_csv = "new_tfm_uam.csv"
        fieldnames = [
            "Universidad",
            "Tipo Titulación",
            "Facultad",
            "Titulación",
            "Título",
            "Autor",
            "Año",
            "URL",
            "Archivo Abstract",
            "Palabras Clave",
            "Idioma Abstract"
        ]
        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in all_item_links:
                item_url = item["url"]
                tipo = item["tipo"]
                log_message(f"Procesando ítem: {item_url} ({tipo})")
                meta = get_metadata_full(driver, item_url, tipo)
                if meta:
                    writer.writerow(meta)
                    log_message(f"Metadatos guardados para: {item_url}")
                else:
                    log_message(f"No se pudo extraer metadatos de: {item_url}")

        driver.quit()
        log_message("Proceso finalizado.")

class UnedScraper:
    def main(self):
        import os
        import time
        import csv
        import re
        import logging
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup

        # Configuración de logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger()

        def log_message(msg):
            logger.info(msg)
            print(msg)

        def setup_driver():
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)

        def obtener_html(driver, url):
            try:
                driver.get(url)
                time.sleep(3)
                return driver.page_source
            except Exception as e:
                log_message(f"Error al acceder a {url} - {e}")
                return None

        def extraer_metadatos(html, url, carpeta_abstracts):
            soup = BeautifulSoup(html, 'html.parser')
            texto_completo = soup.get_text(separator="\n")

            def get_meta_value(key):
                td = soup.find("td", text=lambda t: t and key in t)
                if td:
                    sibling = td.find_next_sibling("td")
                    if sibling:
                        return sibling.get_text(strip=True)
                pattern = re.compile(rf"{re.escape(key)}\s*[:\-]\s*(.*)", re.IGNORECASE)
                match = pattern.search(texto_completo)
                return match.group(1).strip() if match else ""

            universidad = get_meta_value("dc.publisher")
            tipo_titulacion = ""
            colecciones = soup.find("ds-item-page-collections")
            if colecciones:
                span = colecciones.find("span")
                if span:
                    tipo_titulacion = re.sub(r"^Colecciones", "", span.get_text(strip=True)).strip()

            facultad = get_meta_value("dc.relation.center")
            titulacion = get_meta_value("dc.relation.degree")
            titulo = get_meta_value("dc.title")
            if not titulo and soup.title:
                titulo = soup.title.get_text(strip=True)
            if not titulo:
                titulo = "Título no disponible"

            autor = get_meta_value("dc.contributor.author")
            fecha = get_meta_value("dc.date.issued")
            anio = fecha.split("-")[0] if fecha else ""
            palabras = soup.find_all("td", text=lambda t: t and t.strip() == "dc.subject.keywords")
            lista_palabras = [td.find_next_sibling("td").get_text(strip=True) for td in palabras if td.find_next_sibling("td")]
            palabras_clave = ", ".join(lista_palabras)
            idioma = get_meta_value("dc.language.iso")

            titulo_safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', titulo)[:30]
            hash_id = abs(hash(titulo)) % (10 ** 8)
            abstract_text = get_meta_value("dc.description.abstract")
            if not abstract_text:
                abstract_text = "Resumen no disponible"
            prefijo = "RND_" if abstract_text == "Resumen no disponible" else ""
            archivo_abstract = f"{prefijo}{titulo_safe}_{anio}_{hash_id}.txt"

            os.makedirs(carpeta_abstracts, exist_ok=True)
            ruta_abstract = os.path.join(carpeta_abstracts, archivo_abstract)
            try:
                with open(ruta_abstract, "w", encoding="utf-8") as f:
                    f.write(abstract_text)
                log_message(f"Abstract guardado en {ruta_abstract}")
            except Exception as e:
                log_message(f"Error al guardar abstract: {e}")
                ruta_abstract = ""

            return {
                "Universidad": universidad,
                "Tipo Titulación": tipo_titulacion,
                "Facultad": facultad,
                "Titulación": titulacion,
                "Título": titulo,
                "Autor": autor,
                "Año": anio,
                "URL": url,
                "Archivo Abstract": ruta_abstract,
                "Palabras Clave": palabras_clave,
                "Idioma Abstract": idioma
            }

        def cargar_urls_procesadas(archivo):
            if os.path.exists(archivo):
                with open(archivo, "r", encoding="utf-8") as f:
                    return set(line.strip() for line in f)
            return set()

        def guardar_url_procesada(archivo, url):
            with open(archivo, "a", encoding="utf-8") as f:
                f.write(url + "\n")

        def procesar_coleccion(nombre, base_url, max_paginas, carpeta_abstracts, archivo_csv, archivo_checkpoint):
            driver = setup_driver()
            urls_procesadas = cargar_urls_procesadas(archivo_checkpoint)
            detail_urls = set()

            for page in range(1, max_paginas + 1):
                url_listing = base_url.format(page)
                log_message(f"[{nombre}] Procesando listado: {url_listing}")
                html_listing = obtener_html(driver, url_listing)
                if html_listing:
                    soup = BeautifulSoup(html_listing, 'html.parser')
                    links = soup.find_all("a", class_="ng-star-inserted")
                    for link in links:
                        href = link.get('href')
                        if href and href.startswith("/entities/publication"):
                            full_url = "https://e-spacio.uned.es" + href + "/full"
                            if full_url not in urls_procesadas:
                                detail_urls.add(full_url)
                time.sleep(1)

            log_message(f"[{nombre}] Total URLs a procesar: {len(detail_urls)}")

            fieldnames = ["Universidad", "Tipo Titulación", "Facultad", "Titulación", "Título", 
                          "Autor", "Año", "URL", "Archivo Abstract", "Palabras Clave", "Idioma Abstract"]

            modo_csv = "a" if os.path.exists(archivo_csv) else "w"
            with open(archivo_csv, modo_csv, newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if modo_csv == "w":
                    writer.writeheader()

                for url in detail_urls:
                    log_message(f"[{nombre}] Detalle: {url}")
                    html = obtener_html(driver, url)
                    if html:
                        metadatos = extraer_metadatos(html, url, carpeta_abstracts)
                        writer.writerow(metadatos)
                        guardar_url_procesada(archivo_checkpoint, url)
                    else:
                        log_message(f"[{nombre}] Error con URL: {url}")

            driver.quit()
            log_message(f"[{nombre}] Finalizado.")

        def main():
            colecciones = [
                {
                    "nombre": "TFG",
                    "base_url": "https://e-spacio.uned.es/collections/12dc858e-4c48-4ded-9e12-11d28bebd503?cp.page={}",
                    "carpeta_abstracts": "abstracts_tfg",
                    "archivo_csv": "trabajos_tfg.csv",
                    "archivo_checkpoint": "urls_procesadas_tfg.txt"
                },
                {
                    "nombre": "TFM",
                    "base_url": "https://e-spacio.uned.es/collections/cbc92535-7b5a-457f-9e69-e0485e5ef80a?cp.page={}",
                    "carpeta_abstracts": "abstracts_tfm",
                    "archivo_csv": "trabajos_tfm.csv",
                    "archivo_checkpoint": "urls_procesadas_tfm.txt"
                }
            ]
            for col in colecciones:
                procesar_coleccion(
                    nombre=col["nombre"],
                    base_url=col["base_url"],
                    max_paginas=100,
                    carpeta_abstracts=col["carpeta_abstracts"],
                    archivo_csv=col["archivo_csv"],
                    archivo_checkpoint=col["archivo_checkpoint"]
                )

        if __name__ == "__main__":
            main()


class UnileonScraper:
    def main(self):
        import os
        import time
        import csv
        import re
        import logging
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            filename='scraper.log', filemode='w')
        logger = logging.getLogger()

        def log_message(msg):
            logger.info(msg)
            print(msg)

        def setup_driver():
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver

        def obtener_html(driver, url):
            try:
                driver.get(url)
                time.sleep(3)
                html = driver.page_source
                log_message(f"Página descargada: {url}")
                return html
            except Exception as e:
                log_message(f"Error al obtener HTML de {url}: {e}")
                return None

        def extraer_titulaciones_paginacion(driver, url):
            titulaciones = []
            driver.get(url)
            time.sleep(3)
            while True:
                tit_elements = driver.find_elements(By.XPATH, "//td[@class='ds-table-cell odd']/a")
                for elem in tit_elements:
                    nombre = elem.text.strip()
                    link = elem.get_attribute("href")
                    if link.startswith("/"):
                        link = "https://buleria.unileon.es" + link
                    titulaciones.append({"nombre": nombre, "url": link})
                try:
                    siguiente_btn = driver.find_element(By.XPATH, "//li[@class='next pull-right']/a")
                    driver.execute_script("arguments[0].click();", siguiente_btn)
                    time.sleep(3)
                except Exception as e:
                    log_message("No se encontró botón 'Siguiente'. Fin de la paginación.")
                    break
            return titulaciones

        def obtener_trabajos_titulacion(driver, tit_url):
            trabajos = []
            driver.get(tit_url)
            time.sleep(3)
            while True:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                page_trabajos = []
                artifact_divs = soup.find_all("div", class_="artifact-item")
                for div in artifact_divs:
                    a_tag = div.find("a", href=True)
                    if a_tag:
                        titulo = a_tag.get_text(strip=True)
                        url = a_tag.get("href")
                        if url.startswith("/"):
                            url = "https://buleria.unileon.es" + url
                        page_trabajos.append({"titulo": titulo, "url": url})
                if not page_trabajos:
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag.get("href")
                        if "/handle/" in href:
                            titulo = a_tag.get_text(strip=True)
                            if titulo:
                                if href.startswith("/"):
                                    href = "https://buleria.unileon.es" + href
                                page_trabajos.append({"titulo": titulo, "url": href})
                trabajos.extend(page_trabajos)
                try:
                    siguiente_btn = driver.find_element(By.XPATH, "//li[@class='next pull-right']/a")
                    driver.execute_script("arguments[0].click();", siguiente_btn)
                    time.sleep(3)
                except Exception as e:
                    log_message("No se encontró botón 'Siguiente' para trabajos. Fin de la paginación en esta titulación.")
                    break
            return trabajos

        def extraer_metadatos(html, url, tipo_titulacion, titulacion):
            soup = BeautifulSoup(html, 'html.parser')
            metadatos = {
                "Universidad": "Universidad de Huelva",
                "Tipo Titulación": tipo_titulacion,
                "Facultad": "No disponible",
                "Titulación": titulacion,
                "Título": "No disponible",
                "Autor": "No disponible",
                "Año": "No disponible",
                "URL": url.split("?")[0],
                "Archivo Abstract": "",
                "Palabras Clave": "",
                "Idioma Abstract": "No disponible"
            }
            tabla = soup.find("table", class_="ds-includeSet-table")
            if not tabla:
                log_message("No se encontró la tabla de metadatos en la página full.")
                return metadatos

            filas = tabla.find_all("tr")
            abstract_es = None
            palabras = []
            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) >= 2:
                    campo = celdas[0].get_text(strip=True)
                    valor = celdas[1].get_text(" ", strip=True)
                    if campo.lower() == "dc.title":
                        metadatos["Título"] = valor
                    elif campo.lower() == "dc.contributor.author":
                        metadatos["Autor"] = valor
                    elif campo.lower() == "dc.date.issued":
                        metadatos["Año"] = valor[:4]
                    elif campo.lower() == "dc.description.abstract":
                        if abstract_es is None:
                            abstract_es = valor
                            metadatos["Idioma Abstract"] = "spa"
                    elif campo.lower() == "dc.subject.other":
                        if not re.search(r"\\b(Fear|Coping|Nursing|Attitudes|Palliative|End-of-life)\\b", valor, re.IGNORECASE):
                            palabras.append(valor)
            if abstract_es is not None:
                metadatos["Archivo Abstract"] = guardar_abstract(abstract_es, metadatos["Título"], metadatos["Año"], tipo_titulacion)
            if palabras:
                metadatos["Palabras Clave"] = ", ".join(palabras)
            return metadatos

        def guardar_abstract(abstract_text, titulo, anio, tipo_titulacion):
            if not abstract_text.strip():
                abstract_text = "RND"
            carpeta = f"abstracts_uhu_{tipo_titulacion}"
            os.makedirs(carpeta, exist_ok=True)
            titulo_safe = re.sub(r'[^a-zA-Z0-9_\\-]', '_', titulo)[:30]
            hash_id = abs(hash(titulo)) % (10**8)
            filename = f"{titulo_safe}_{anio}_{hash_id}.txt"
            ruta = os.path.join(carpeta, filename)
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(abstract_text)
                log_message(f"Abstract guardado en {ruta}")
            except Exception as e:
                log_message(f"Error al guardar abstract: {e}")
                ruta = ""
            return ruta

        driver = setup_driver()
        url_titulaciones = "https://buleria.unileon.es/browse?type=titulacion"
        
        log_message("Extrayendo titulaciones con paginación...")
        titulaciones = extraer_titulaciones_paginacion(driver, url_titulaciones)
        log_message(f"Total titulaciones encontradas: {len(titulaciones)}")
        
        grupos = {"TFM": [], "TFG": []}
        for tit in titulaciones:
            nombre = tit["nombre"].strip().lower()
            if nombre.startswith("máster") or nombre.startswith("master"):
                grupos["TFM"].append(tit)
            elif nombre.startswith("grado"):
                grupos["TFG"].append(tit)
        
        log_message(f"Titulaciones clasificadas para TFM: {len(grupos['TFM'])}")
        log_message(f"Titulaciones clasificadas para TFG: {len(grupos['TFG'])}")
        
        fieldnames = ["Universidad", "Tipo Titulación", "Facultad", "Titulación",
                      "Título", "Autor", "Año", "URL", "Archivo Abstract", "Palabras Clave", "Idioma Abstract"]

        for tipo, lista_titulaciones in grupos.items():
            output_csv = f"metadatos_{tipo.lower()}.csv"
            with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                log_message(f"Procesando grupo: {tipo} con {len(lista_titulaciones)} titulaciones")
                
                for tit in lista_titulaciones:
                    log_message(f"Procesando titulación: {tit['nombre']} -> {tit['url']}")
                    trabajos = obtener_trabajos_titulacion(driver, tit["url"])
                    if not trabajos:
                        log_message(f"No se encontraron trabajos en la titulación: {tit['nombre']}")
                        continue

                    for trabajo in trabajos:
                        log_message(f"Procesando trabajo: {trabajo['titulo']} -> {trabajo['url']}")
                        url_item = trabajo['url'] if "show=full" in trabajo['url'] else trabajo['url'] + "?show=full"
                        html_item = obtener_html(driver, url_item)
                        if not html_item:
                            log_message(f"No se pudo descargar la vista full del trabajo: {trabajo['titulo']}")
                            continue

                        meta = extraer_metadatos(html_item, trabajo['url'], tipo, tit['nombre'])
                        writer.writerow(meta)
                        log_message(f"Metadatos guardados para: {trabajo['titulo']}")
                        
            log_message(f"CSV generado: {output_csv}")

        driver.quit()
        log_message("Proceso finalizado.")

if __name__ == "__main__":
    UnedScraper().main()
    UnedScraper().main()
    UnedScraper().main()
