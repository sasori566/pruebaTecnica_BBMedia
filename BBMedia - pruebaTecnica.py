#--------------------------------------------------------------------------------------------------
# PRUEBA TECNICA - BB MEDIA
#
# DESARROLLADOR: Sebastian Bejarano
# 
# SITIO A REALIZAR EL SCRAPING: https://www.plex.tv/
# REPOSITORIO DE GITHUB: https://github.com/sebaezequiel/pruebaTecnica_BBMedia
# 
# ARCHIVOS DE SALIDA: 
# plex_livetv.json (ejemplo de salida en Github)
# plex_ondemand.json (ejemplo de salida en Github)
# 
#
# INSTRUCCIONES PREVIAS A EJECUCIÓN: 
# 1) Configurar ruta de "chromedriver.exe"
# - Descargar archivo "chromedriver.exe" desde Github
# - Colocar en la variable "service" la ruta de ubicación del archivo "chromedriver.exe"
# - La ruta debe declararse de la siguiente manera (con barras invertidas y 'r' al inicio de la ruta): 
#   service = Service(r'C:\Users\Sebastian Bejarano\Downloads\chromedriver-win64\chromedriver.exe')
#
# 2) Instalar las siguientes librerias de Python:
# - pip install requests
# - pip install beautifulsoup4
# - pip install selenium
#
#--------------------------------------------------------------------------------------------------

# -----------------------------
# - DEFINICIÓN DE BIBLIOTECAS -
# -----------------------------

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json


# ---------------------------
# - DEFINICIÓN DE VARIABLES -
# ---------------------------

# Iniciar cronometro Live TV
livetv_inicio = time.time()

# Variable del sitio declarada
url_plex = 'https://www.plex.tv/' 
ruta_latam = 'es/'

# Configurar el servicio de ChromeDriver
service = Service(r'C:\Users\Sebastian Bejarano\Downloads\chromedriver-win64\chromedriver.exe')

# Configurar Chrome en modo headless
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ejecutar en modo headless
chrome_options.add_argument("--disable-gpu")  # Necesario para Windows en modo headless
chrome_options.add_argument("--no-sandbox")  # Evitar problemas de permisos
chrome_options.add_argument("--disable-dev-shm-usage")  # Usar la memoria compartida de manera eficiente

# Inicializar el navegador con las opciones en modo headless
driver = webdriver.Chrome(service=service, options=chrome_options)

# -----------------------------------------
# - DEFINICION DE FUNCIONES PARA SCRAPING -
# -----------------------------------------

# Generar url para Latam
def generar_url_latam(url_plex, ruta_latam):
    url_latam = url_plex.replace('www.', 'watch.') + ruta_latam
    return url_latam

# Generar url para la sección de contenido Live TV
def generar_url_livetv(url_latam):
    url_livetv = url_latam + 'live-tv'
    return url_livetv

# Generar url para la sección de contenido OnDemand
def generar_url_ondemand(url_latam):
    url_ondemand = url_latam + 'on-demand'
    return url_ondemand


# SCRAPING DE CONTENIDO LIVETV
def obtener_canales(url_livetv, url_latam):
    response = requests.get(url_livetv)
    response.raise_for_status() 

    soup = BeautifulSoup(response.text, 'html.parser')
    print("Scraping: Contenido Live TV")

    # Generar diccionario con las url de cada canal
    canales = {}

    for figure in soup.find_all('figure'):
        a_tag = figure.find('a', href=True)
        span_tag = figure.find('span', title=True)

        if a_tag and span_tag:
            nombre_canal = span_tag.get('title')
            href_canal = f"https://watch.plex.tv{a_tag['href']}"
            canales[nombre_canal] = href_canal

    return canales

# Obtener programación de cada canal
def obtener_programas(driver, url, canal):
    driver.get(url)
    
    time.sleep(20) 

    try:
        on_now_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='On Now']"))
        )
        
        # Extraer la programación actual
        on_now_title = driver.find_element(By.XPATH, "//h2[text()='On Now']/following-sibling::span").text
        on_now_title = on_now_title if on_now_title.strip() else "No disponible"
        
        up_next_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Up Next']"))
        )
        
        # Extraer la programación siguiente
        up_next_times = driver.find_elements(By.XPATH, "//div[contains(@class, 'ChannelAiringsList_airingTime')]//span")
        up_next_titles = driver.find_elements(By.XPATH, "//div[contains(@class, 'ChannelAiringsList_airingTime')]/following-sibling::span")

        up_next_programming = {}
        if up_next_times and up_next_titles:
            for time_element, title_element in zip(up_next_times, up_next_titles):
                time_text = time_element.text if time_element.text.strip() else "No disponible"
                title_text = title_element.text if title_element.text.strip() else "No disponible"
                up_next_programming[time_text] = title_text
        else:
            up_next_programming = {"No disponible": "No disponible"}

        # Generar diccionario con la metadata de cada canal
        programacion = {
            "Programación actual": on_now_title,
            "A continuación": up_next_programming
        }

    except Exception as e:
        print(f"Error extrayendo la programación: {e}")
        programacion = {
            "Programación actual": "No disponible",
            "A continuación": {"No disponible": "No disponible"}
        }

    return programacion


# Obtener metadata de contenido Live TV
def obtener_data_canales(canales):
    chromedriver_path = "C:\\Users\\Sebastian Bejarano\\Downloads\\chromedriver-win64\\chromedriver.exe"

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Abrir navegador maximizado
    chrome_options.add_argument("--headless")  # Modo headless para que no se abra el navegador físicamente

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Diccionario para almacenar la programación de todos los canales
    contenido_livetv = {}

    try:
        for nombre_canal, url in canales.items():
            driver.get(url)
            
            time.sleep(30) 

            html_completo = driver.page_source
            soup = BeautifulSoup(html_completo, "html.parser")
            html_ordenado = soup.prettify() 

            programacion = obtener_programas(driver, url, nombre_canal)
            contenido_livetv[nombre_canal] = programacion  

            time.sleep(30)

    except Exception as e:
        print(f"Error al guardar el HTML: {e}")
    
    finally:
        driver.quit()

    print("Fin de Scraping: Contenido Live TV")
    return contenido_livetv


# SCRAPING DE CONTENIDO ONDEMAND
def obtener_categorias(url_plex, ondemand_url):
    response = requests.get(ondemand_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    print("Scraping: Categorías de contenido OnDemand")

    # Generar diccionario con las url de cada categoría de contenido OnDemand
    categorias = {
        'action': '',
        'animation': '',
        'comedy': '',
        'crime': '',
        'descriptive-audio': '',
        'documentary': '',
        'drama': '',
        'en-espanol': '',
        'horror': '',
        'musical': '',
        'romance': '',
        'sci-fi': '',
        'thriller': '',
        'western': ''
    }
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/on-demand/category/' in href:
            for categoria in categorias:
                if f'/on-demand/category/{categoria}' in href:
                    categorias[categoria] = urljoin(ondemand_url, href)
    print(categorias)
    return categorias


# Limpiar data para Json
def limpiar_texto(texto):
    texto_limpio = texto.replace('\"', '')  
    return texto_limpio

# Obtener metadata de peliculas
def obtener_data_pelicula(contenido_ondemand):
    datos_peliculas = {}
    
    # Filtrar urls y tomar las que direccionen a peliculas
    peliculas_filtradas = {titulo: url for titulo, url in contenido_ondemand.items() if "movie" in url}
    
    for titulo, url in peliculas_filtradas.items():
        respuesta = requests.get(url)
        time.sleep(30)

        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            try:
                titulo_pelicula = soup.find('h1', {'data-testid': 'metadata-title'}).get_text(strip=True)
            except AttributeError:
                titulo_pelicula = 'No disponible'

            try:
                director_span = soup.find('span', {'data-testid': 'metadata-tagline'})
                director = director_span.find('a').get_text(strip=True) if director_span else 'No disponible'
            except AttributeError:
                director = 'No disponible'

            try:
                metadata_line = soup.find('span', {'data-testid': 'metadata-line1'})
                spans = metadata_line.find_all('span') if metadata_line else []
                año = spans[0].get_text(strip=True) if len(spans) > 0 else 'No disponible'
                duracion = spans[1].get_text(strip=True) if len(spans) > 1 else 'No disponible'
                clasificacion = spans[2].get_text(strip=True) if len(spans) > 2 else 'No disponible'
            except (AttributeError, IndexError):
                año, duracion, clasificacion = 'No disponible', 'No disponible', 'No disponible'

            try:
                genero_elements = soup.find('span', {'data-testid': 'metadata-line2'}).find_all('a')
                generos = [gen.get_text(strip=True) for gen in genero_elements]
                genero = ','.join(generos)
            except AttributeError:
                genero = 'No disponible'

            try:
                descripcion = soup.find('div', class_='casrwa1 casrwa2').get_text(strip=True)
                descripcion = limpiar_texto(descripcion)
            except AttributeError:
                descripcion = 'No disponible'

            try:
                script_tag = soup.find('script', type='application/ld+json')
                if script_tag:
                    json_data = json.loads(script_tag.string)
                    actores = json_data.get('actor', [])
                    reparto = [actor['name'] for actor in actores]
                else:
                    reparto = ['No disponible']
            except (json.JSONDecodeError, KeyError, TypeError):
                reparto = ['No disponible']

            # Generar diccionario con la metadata de cada pelicula
            datos_peliculas[titulo_pelicula] = {
                'Director': director,
                'Año': año,
                'Duración': duracion,
                'Género': genero,
                'Clasificación': clasificacion,
                'Descripción': descripcion,
                'Reparto': ', '.join(reparto),
                'Link': url
            }
        else:
            datos_peliculas[titulo] = {'Error': f'Error en la solicitud. Código de estado: {respuesta.status_code}'}

    return datos_peliculas


# Extraer url de las temporadas de cada serie
def extract_season_urls(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    
    all_links = soup.find_all('a', href=True)
    
    base_url = 'https://watch.plex.tv'
    season_urls = []
    
    for link in all_links:
        href = link['href']
        if "season" in href.lower():
            full_url = base_url + href if not href.startswith('http') else href
            season_urls.append(full_url)
    
    return season_urls


# Obtener metadata de cada temporada de cada serie
def obtener_data_temporadas(season_urls):
    datos_temporadas = {}
    
    for url in season_urls:
        respuesta = requests.get(url)

        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            try:
                temporada = soup.find('h1', {'data-testid': 'metadata-title'}).get_text(strip=True)
            except AttributeError:
                temporada = 'No disponible'
            
            episodios = {}
            
            episode_elements = soup.find_all('a', {'aria-label': True})
            
            # Generar diccionario con la metadata de los episodios
            for episode in episode_elements:
                aria_label = episode.get('aria-label', '')
                if 'Episode' in aria_label:
                    parts = aria_label.split('·')
                    if len(parts) >= 3:
                        numero_episodio = parts[1].strip()
                        nombre_episodio = parts[2].strip()
                        episodios[numero_episodio] = {
                            'Nombre': nombre_episodio,
                            'URL': episode['href']
                        }
            
            datos_temporadas[url] = episodios if episodios else {'No disponible': 'No disponible'}
            time.sleep(30)
        else:
            datos_temporadas[url] = {'Error': f'Error en la solicitud. Código de estado: {respuesta.status_code}'}
            time.sleep(30)

    return datos_temporadas


# Obtener url de cada episodio por temporada
def obtener_url_episodios(season_urls):
    all_episode_urls = []
    
    for season_url in season_urls:
        try:
            respuesta = requests.get(season_url)
            respuesta.raise_for_status()
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            episode_section = soup.find('div', class_='_1tl8vr30')
            if not episode_section:
                print(f"No se encontró la sección de episodios en {season_url}.")
                continue
            
            episode_links = episode_section.find_all('a', href=True)
            
            for link in episode_links:
                href = link.get('href')
                if href:
                    url_completa = f'https://watch.plex.tv{href}'
                    all_episode_urls.append(url_completa)
        
        except requests.RequestException as e:
            print(f"Error al obtener la URL de la temporada {season_url}: {e}")
    
    return all_episode_urls

# Obtener metadata de episodios
def obtener_data_episodios(all_episode_urls):
    datos_episodios = {}

    for url in all_episode_urls:
        respuesta = requests.get(url)
        time.sleep(30)
        
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')

            try:
                titulo = soup.find('h2', {'data-testid': 'metadata-subtitle'}).get_text(strip=True)
            except AttributeError:
                titulo = 'No disponible'

            try:
                descripcion = soup.find('div', {'class': 'casrwa1 casrwa2'}).get_text(strip=True)
                descripcion = limpiar_texto(descripcion)
            except AttributeError:
                descripcion = 'No disponible'

            try:
                duracion = soup.find('span', {'data-testid': 'metadata-line1'}).find_all('span')[2].get_text(strip=True)
            except (AttributeError, IndexError):
                duracion = 'No disponible'

            try:
                fecha_emision = soup.find('span', {'data-testid': 'metadata-line1'}).find_all('span')[1].get_text(strip=True)
            except (AttributeError, IndexError):
                fecha_emision = 'No disponible'


            # Generar diccionario con la metadata de los episodios
            datos_episodios[url] = {
                'Título del episodio': titulo,
                'Descripción del episodio': descripcion,
                'Duración del episodio': duracion,
                'Fecha de emisión del episodio': fecha_emision
            }
        else:
            datos_episodios[url] = {'Error': f'Error en la solicitud. Código de estado: {respuesta.status_code}'}

    return datos_episodios


# Obtener metadata de las series
def obtener_data_shows(contenido_ondemand):
    datos_series = {}
    
    # Filtrar urls y tomar las que direccionen a series
    series_filtradas = {titulo: url for titulo, url in contenido_ondemand.items() if "show" in url}
    
    for titulo, url in series_filtradas.items():
        respuesta = requests.get(url)
        time.sleep(30)

        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            try:
                titulo_serie = soup.find('h1', {'data-testid': 'metadata-title'}).get_text(strip=True)
            except AttributeError:
                titulo_serie = 'No disponible'

            try:
                metadata_line = soup.find('span', {'data-testid': 'metadata-line1'})
                spans = metadata_line.find_all('span') if metadata_line else []
                año = spans[0].get_text(strip=True) if len(spans) > 0 else 'No disponible'
                clasificacion = spans[2].get_text(strip=True) if len(spans) > 2 else 'No disponible'
            except (AttributeError, IndexError):
                año, clasificacion = 'No disponible', 'No disponible'

            try:
                genero_elements = soup.find('span', {'data-testid': 'metadata-line2'}).find_all('a')
                generos = [gen.get_text(strip=True) for gen in genero_elements]
                genero = ','.join(generos)
            except AttributeError:
                genero = 'No disponible'

            try:
                descripcion = soup.find('div', class_='casrwa1 casrwa2').get_text(strip=True)
                descripcion = limpiar_texto(descripcion)
            except AttributeError:
                descripcion = 'No disponible'

            try:
                script_tag = soup.find('script', type='application/ld+json')
                if script_tag:
                    json_data = json.loads(script_tag.string)
                    actores = json_data.get('actor', [])
                    reparto = [actor['name'] for actor in actores]
                else:
                    reparto = ['No disponible']
            except (json.JSONDecodeError, KeyError, TypeError):
                reparto = ['No disponible']

            season_urls = extract_season_urls(respuesta.text)
            datos_temporadas = obtener_data_temporadas(season_urls)
            print(season_urls)
            episode_urls = obtener_url_episodios(season_urls)
            datos_episodios = obtener_data_episodios(episode_urls)

            # Generar diccionario con la metadata de las series
            datos_series[titulo_serie] = {
                'Año': año,
                'Género': genero,
                'Clasificación': clasificacion,
                'Descripción': descripcion,
                'Reparto': ', '.join(reparto),
                'Link': url,
                'Datos de episodios' : datos_episodios
            }
        else:
            datos_series[titulo] = {'Error': f'Error en la solicitud. Código de estado: {respuesta.status_code}'}

    return datos_series


# Obtener todas las categorias del contenido OnDemand
def obtener_href_ondemand(categorias,url_plex):
    series_ondemand = {}
    peliculas_ondemand = {}
    
    for categoria, url in categorias.items():
        response = requests.get(url)
        time.sleep(20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            enlaces = soup.find_all('a', href=True)
            
            for enlace in enlaces:
                href = enlace['href']
                titulo = enlace.text.strip()
                
                if not href.startswith('http'):
                    href = url_plex.replace('www.plex.tv/','watch.plex.tv') + href
                
                # Clasificación en series o películas
                if '/show/' in href:
                    series_ondemand[titulo] = href
                elif '/movie/' in href:
                    peliculas_ondemand[titulo] = href
                time.sleep(20)

    return series_ondemand, peliculas_ondemand


# Exportar contenido Live Tv en formato Json
def exportar_livetv(contenido_livetv, tiempo_ejecucion_livetv, nombre_archivo="plex_livetv.json"):
    livetv_dict = {
        "Live TV": contenido_livetv,
        "Tiempo de ejecución": f"{int(tiempo_ejecucion_livetv)} minutos"
    }
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo_json:
            json.dump(livetv_dict, archivo_json, ensure_ascii=False, indent=4)
        print(f"Archivo {nombre_archivo} exportado exitosamente.")
    except Exception as e:
        print(f"Error al exportar el archivo JSON: {e}")

# # Exportar contenido OnDemand en formato Json
def exportar_ondemand(datos_peliculas, datos_series, tiempo_ejecucion_ondemand, nombre_archivo="plex_ondemand.json"):
    ondemand_dict = {
        "OnDemand": {
            "Peliculas": datos_peliculas,
            "Series": datos_series
        },
        "Tiempo de ejecución": f"{int(tiempo_ejecucion_ondemand)} minutos"
    }
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo_json:
            json.dump(ondemand_dict, archivo_json, ensure_ascii=False, indent=4)
        print(f"Archivo {nombre_archivo} exportado exitosamente.")
    except Exception as e:
        print(f"Error al exportar el archivo JSON: {e}")


#--------------------------
#- EJECUCIÓN DE FUNCIONES -
#--------------------------

# Obtener url a scrapear
url_latam = generar_url_latam(url_plex, ruta_latam)
url_livetv = generar_url_livetv(url_latam)
url_ondemand = generar_url_ondemand(url_latam)


# Scraping de contenido Live TV
canales = obtener_canales(url_livetv, url_latam)
contenido_livetv = obtener_data_canales(canales)

# Finalizar cronometro LiveTV
livetv_fin = time.time()
tiempo_ejecucion_livetv = (livetv_fin - livetv_inicio) // 60

# Exportar contenido Live TV en formato Json
exportar_livetv(contenido_livetv,tiempo_ejecucion_livetv)

# Iniciar cronometro OnDemand
ondemand_inicio = time.time()

# Scraping de contenido OnDemand
categorias = obtener_categorias(url_plex, url_ondemand)
try:
    series_ondemand,peliculas_ondemand = obtener_href_ondemand(categorias)
finally:
    driver.quit()


datos_peliculas = obtener_data_pelicula(peliculas_ondemand)
datos_series = obtener_data_shows(series_ondemand)

# Finalizar cronometro OnDemand
ondemand_fin = time.time()
tiempo_ejecucion_ondemand = (ondemand_inicio - ondemand_fin) // 60


# Exportar los datos a un archivo JSON
exportar_ondemand(datos_peliculas, datos_series, tiempo_ejecucion_ondemand)

# Tiempo de ejecucion total
tiempo_ejecucion_total = (ondemand_fin - livetv_inicio) // 60

print("Finalizado scraping de Plex.tv")
print(f"Tiempo de ejecucion total : {int(tiempo_ejecucion_total)} minutos")
