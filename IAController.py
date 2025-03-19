from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename

# Importar funciones desde tu módulo existente de IA
from Modular_IA import extraer_texto_con_tesseract, busqueda_codigo_relajado, busqueda_texto_relajado

from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Configuración para subir archivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'heif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/procesar-imagen', methods=['POST'])
def procesar_imagen():
    # Validar que se haya enviado el archivo 'imagen'
    if 'imagen' not in request.files:
        ##print("No se encontró ninguna imagen.")
        return jsonify({"error": "No se encontró ninguna imagen"}), 400
    
    archivo = request.files['imagen']
    
    if archivo.filename == '':
        ##print("No se seleccionó ningún archivo.")
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400
    
    if archivo and allowed_file(archivo.filename):
        # Guardar temporalmente la imagen
        filename = secure_filename(archivo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            archivo.save(filepath)
            ##print(f"Archivo guardado en: {filepath}")
        except Exception as e:
            ##print(f"Error al guardar el archivo: {e}")
            return jsonify({"error": "Error al guardar el archivo"}), 500

        # Intentar extraer el texto de la imagen usando tu función de IA
        try:
            ##print("Intentando extraer texto de la imagen...")
            texto1, texto2 = extraer_texto_con_tesseract(filepath)
            ##print("Texto extraído:", texto1, texto2)
        except Exception as e:
            ##print(f"Error al extraer texto: {e}")
            return jsonify({"error": "Error al extraer texto"}), 500

        # Recuperar los datos ingresados por el usuario desde request.form
        tipoCuenta_input = request.form.get('tipoCuenta', '').strip().lower()
        name_input = request.form.get('name', '').strip().lower()
        lastname_input = request.form.get('lastname', '').strip().lower()

        if(tipoCuenta_input == 'participante'):
            escuela_input = request.form.get('escuela', '').strip().lower()
            codigo_input = request.form.get('codigo_asesor', '').strip().lower()           

        # Concatenar ambos textos extraídos para una comparación más completa
        texto_combinado = (texto1 + " " + texto2).lower()

        # Evaluar cada campo:
        # Para 'nombre', 'apellido' y 'escuela' usamos busqueda_texto_relajado,
        # para 'codigo' usamos busqueda_codigo_relajado.
        nombre_valido = busqueda_texto_relajado(name_input, texto_combinado)
        apellido_valido = busqueda_texto_relajado(lastname_input, texto_combinado)

        if(tipoCuenta_input == 'participante'):
            escuela_valida = busqueda_texto_relajado(escuela_input, texto_combinado)
            codigo_valido = busqueda_codigo_relajado(codigo_input, texto_combinado)

        # Eliminar la imagen temporal
        try:
            os.remove(filepath)
            ##print(f"Archivo {filename} eliminado después de la validación.")
        except Exception as e:
            ##print(f"Error al eliminar el archivo: {e}")
            return jsonify({"error": "Error al eliminar el archivo"}), 500

        # Devolver los valores booleanos al controlador
        if(tipoCuenta_input == 'asesor'):
            return jsonify({
                "nombre_valido": nombre_valido,
                "apellido_valido": apellido_valido,
            })
        elif(tipoCuenta_input == 'participante'):
            return jsonify({
                "nombre_valido": nombre_valido,
                "apellido_valido": apellido_valido,
                "escuela_valida": escuela_valida,
                "codigo_valido": codigo_valido
            })
    else:
        return jsonify({"error": "Archivo no permitido"}), 400

if __name__ == '__main__':
    app.run(debug=True)
