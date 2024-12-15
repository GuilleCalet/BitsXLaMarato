# Configuración de la carpeta QR
import os
import sqlite3  # Biblioteca para trabajar con SQLite
from flask import Flask, render_template, request

app = Flask(__name__)

QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')  # Ruta absoluta del sistema
os.makedirs(QR_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

# Configuración de la base de datos
DATABASE = os.path.join(app.root_path, 'database.db')
DATABASE2 = os.path.join(app.root_path, 'database2.db')  # Nueva base de datos

@app.route('/')
def index():
    return render_template('index.html')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Crear tabla pacientes original
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            edad INTEGER,
            diagnostico TEXT,
            qr_path TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
def init_db_new():
    conn = sqlite3.connect(DATABASE2)
    cursor = conn.cursor()
    # Crear tabla pacientes2 en la nueva base de datos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes2 (
            dni TEXT PRIMARY KEY,
            nombre TEXT,
            edad INTEGER,
            diagnostico TEXT,
            seguridad_social TEXT,
            correo TEXT,
            qr_path TEXT
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/generate', methods=['POST'])
def generate_qr():
    # Recoger datos del formulario
    nombre = request.form['nombre']
    edad = request.form['edad']
    diagnostico = request.form['diagnostico']
    seguridad_social = request.form['seguridad_social']
    correo = request.form['correo']
    dni = request.form['dni']

    # Usar la IP local en lugar de request.host_url
    base_url = "http://192.168.116.1:5000"  # Cambia request.host_url por tu IP local
    paciente_url = f"{base_url}/paciente/{dni}"  # URL dinámica para el paciente


    # Ruta para guardar el QR
    qr_filename = f"{dni}.png"
    qr_path_full = os.path.join(QR_FOLDER, qr_filename)
    qr_path = f"/static/qr_codes/{qr_filename}"

    # Guardar los datos en la base de datos
    conn = sqlite3.connect(DATABASE2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pacientes2 (dni, nombre, edad, diagnostico, seguridad_social, correo, qr_path) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (dni, nombre, edad, diagnostico, seguridad_social, correo, qr_path))
    conn.commit()
    conn.close()

    # Crear el QR
    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(paciente_url)  # La URL se incluye como dato en el QR
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar la imagen
    img.save(qr_path_full)

    return render_template('qr.html', nombre=nombre, qr_path=qr_path)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/paciente/<dni>')
def paciente_detail(dni):
    # Consultar datos del paciente desde la base de datos
    conn = sqlite3.connect(DATABASE2)
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, edad, diagnostico, seguridad_social, correo FROM pacientes2 WHERE dni = ?', (dni,))
    paciente = cursor.fetchone()
    conn.close()

    if paciente:
        return render_template('paciente_detail.html', paciente=paciente, dni=dni)
    else:
        return "<h1>Paciente no encontrado</h1>", 404


@app.route('/valoracion_nml_guardia')
def valoracion_nml_guardia():
    return render_template('valoracion_nml_guardia.html')

@app.route('/valoracion_urgencias')
def valoracion_urgencias():
    pasos = [
        "1. Realizar analítica urgente, incluyendo:",
        "   1.1. Bioquímica (análisis de parámetros químicos)",
        "   1.2. Hemograma (análisis de células de la sangre)",
        "   1.3. Coagulación (estudio de la coagulación)",
        "2. Gasometría arterial (PaO2/FiO2)",
        "3. ECG (electrocardiograma)",
        "4. Radiografía de tórax (RxTorax)",
    ]
    return render_template('proves_urgencies.html', pasos=pasos)
@app.route('/radiografia_torax')
def radiografia_torax():
    pruebas = [
        "1. Micro: Esput (gram i cultiu, fongs/microbacteris)",
        "2. Antigenúria: (pneumococ/legionella)",
        "3. 2 Hemocultius",
        "4. Si sospita grip: PCR virus Influenza A i B ",
    ]
    return render_template('radiografia_torax.html', pruebas=pruebas)

@app.route('/dx_concret_no_pneumonia')
def dx_concret_no_pneumonia():
    pasos = [
        "IMMUNOSUPRIMIT IMMUNOCOMPENTENT",
        "OXIGENOTERAPIA ajustant FIO2 segons requeriments (SatO2 > 92%).",
        "INHIBIDOR BOMBA PROTONS (Omeprazol 20 mg/12-24h e.v.)",
        "N-ACETILCISTEÏNA 600 mg/8h v.o. (potent antioxidant pulmonar).",
        "Només si fumadors/exfumadors: nebulitzacions amb 1,5-2cc atrovent + 2cc SF +/- 0,5cc salbutamol (si no Hipertensió Pulmonar).",
        "MORFINA 2,5-5mg s.c. puntual si dispnea intensa.",
        "HBPM: Bemiparina 2500-3500 UI/0,2 mL (segons Kg pes) s.c./dia",
        "METILPREDNISOLONA (en casos específics): ½-1 mg/Kg pes/d e.v + CALCI + Vit D 500mg/400 UI: 2 comp/d v.o.",
        "LOSARTAN 50mg/24h v.o. (antiapoptòtic epitelial). Tan sols si sospita dany epitelial alveolar i no hipoTA)."
    ]
    return render_template('dx_concret_no_pneumonia.html', pasos=pasos)


@app.route('/dx_concret_pneumonia')
def dx_concret_pneumonia():
    return render_template('dx_concret_pneumonia.html')

@app.route('/dx_no_concret')
def dx_no_concret():
    return render_template('dx_no_concret.html')

@app.route('/pacientes')
def ver_pacientes():
    # Consultar datos desde la base de datos database2.db
    conn = sqlite3.connect(DATABASE2)
    cursor = conn.cursor()
    cursor.execute('SELECT dni, nombre, diagnostico, qr_path FROM pacientes2')
    pacientes = cursor.fetchall()
    conn.close()

    # Renderizar la página con los datos de pacientes
    return render_template('paciente.html', pacientes=pacientes)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
