import cv2
import pytesseract
import re
import os
import numpy as np

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Validar extensiones de imagen
def es_formato_valido(ruta, extensiones_validas=(".jpg", ".jpeg", ".png", ".heif")):
    return ruta.lower().endswith(extensiones_validas)

# Preprocesamiento 1: Mejorar imagen
def mejorar_imagen(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gris = cv2.medianBlur(gris, 3)
    kernel = np.ones((2, 2), np.uint8)
    morphed = cv2.morphologyEx(gris, cv2.MORPH_GRADIENT, kernel)
    _, umbralizada = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return umbralizada

# Preprocesamiento 2: Umbral adaptativo
def procesar_umbral_adaptativo(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (5, 5), 0)
    gris = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return gris

# Extraer texto con dos métodos
def extraer_texto_con_tesseract(imagen_ruta):
    if not es_formato_valido(imagen_ruta):
        raise ValueError("Formato no válido. Solo se aceptan jpg, jpeg, png y heif.")
    
    if not os.path.exists(imagen_ruta):
        raise FileNotFoundError("No se encontró la imagen.")

    imagen = cv2.imread(imagen_ruta)

    # Preprocesar usando ambas técnicas
    imagen_mejorada = mejorar_imagen(imagen)
    imagen_umbral = procesar_umbral_adaptativo(imagen)

    # Extraer texto con ambas técnicas
    texto1 = pytesseract.image_to_string(imagen_mejorada, config='--psm 4', lang='spa')
    texto2 = pytesseract.image_to_string(imagen_umbral, config='--psm 6', lang='spa')

    # Limpiar texto
    texto_limpio1 = re.sub(r'\s+', ' ', texto1).strip()
    texto_limpio2 = re.sub(r'\s+', ' ', texto2).strip()

    return texto_limpio1, texto_limpio2

# Buscar texto en registros, adaptado para códigos divididos
def busqueda_codigo_relajado(codigo, texto):
    # Normalizar el texto y el código, eliminando espacios y caracteres no numéricos
    texto_normalizado = re.sub(r'\D', '', texto)  # Solo dejar números
    codigo_normalizado = re.sub(r'\D', '', codigo)
    return codigo_normalizado in texto_normalizado

# Buscar texto relajado para nombre o escuela
def busqueda_texto_relajado(busqueda, texto):
    texto_normalizado = re.sub(r'\W+', ' ', texto.lower())
    busqueda_normalizada = re.sub(r'\W+', ' ', busqueda.lower())
    palabras_texto = set(texto_normalizado.split())
    palabras_busqueda = set(busqueda_normalizada.split())
    return palabras_busqueda.issubset(palabras_texto)

def validar_estudiante_por_campos_separados(registros, texto1, texto2):
    # Variables para guardar los códigos, nombres y escuelas extraídos
    codigos_extraidos = []
    nombres_extraidos = []
    escuelas_extraidas = []

    # Función auxiliar para procesar un texto
    def procesar_texto(texto):
        codigo = None
        nombre = None
        escuela = None

        # Intentar extraer el código (un número de al menos 4 dígitos)
        match_codigo = re.search(r'\b\d{4,}\b', texto)
        if match_codigo:
            codigo = match_codigo.group()

        # Intentar extraer un posible nombre (todo lo que no sea código)
        nombre = re.sub(r'\b\d{4,}\b', '', texto).strip()

        escuela = re.sub(r'\b\d{4,}\b', '', texto).strip()

        return codigo, nombre, escuela

    # Procesar ambos textos y combinar resultados
    codigo1, nombre1, escuela1 = procesar_texto(texto1)
    codigo2, nombre2, escuela2 = procesar_texto(texto2)

    # Agregar códigos, nombres y escuelas extraídos a las listas
    if codigo1:
        codigos_extraidos.append(codigo1)
    if codigo2:
        codigos_extraidos.append(codigo2)
    if nombre1:
        nombres_extraidos.append(nombre1)
    if nombre2:
        nombres_extraidos.append(nombre2)
    if escuela1:
        escuelas_extraidas.append(escuela1)
    if escuela2:
        escuelas_extraidas.append(escuela2)

    # Evaluar si algún código coincide
    codigo_coincide = any(
        busqueda_codigo_relajado(registro['codigo'], codigo)
        for registro in registros
        for codigo in codigos_extraidos
    )

    # Concatenar nombres extraídos para comparar ambos
    nombres_combinados = " ".join(nombres_extraidos)

    # Evaluar si al menos uno de los nombres coincide
    nombre_coincide = any(
        busqueda_texto_relajado(
            f"{registro['nombre']} {registro['apellidos']}", nombres_combinados
        )
        for registro in registros
    )

    # Concatenar escuelas extraídas para comparar
    escuelas_combinadas = " ".join(escuelas_extraidas)

    # Evaluar si al menos una escuela coincide
    escuela_coincide = any(
        busqueda_texto_relajado(
            registro['escuela'], escuelas_combinadas
        )
        for registro in registros
    )

    return codigos_extraidos, nombres_combinados, escuelas_combinadas, codigo_coincide, nombre_coincide, escuela_coincide
