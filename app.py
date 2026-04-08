import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import math
from fpdf import FPDF
import datetime
import json
import tempfile
import os

st.set_page_config(page_title="Cotizador IMAC", page_icon="🍊", layout="centered")

# --- CONEXIÓN SECRETA A GOOGLE SHEETS ---
def conectar_sheets():
    try:
        # Carga los secretos desde la bóveda de Streamlit
        credenciales_dic = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credenciales_dic, scopes=scopes)
        cliente = gspread.authorize(creds)
        # ⚠️ REEMPLAZA ESTO CON TU ID REAL DE GOOGLE SHEETS
        sheet = cliente.open_by_key("1-ns2kgub6g4Mg0gQOr-X1ngodUFMWyrbhf9TEUv1T6c").sheet1
        return sheet
    except Exception as e:
        st.error("Error conectando a la base de datos. Verifica los secretos.")
        return None

# --- ESTILO PARA TABLET Y CELULAR ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #FF6600; color: white; height: 3em; width: 100%; border-radius: 10px; font-size: 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Catálogo
catalogo_rollos = {
    "MASTER LASSER 3.0mm ROJO F.V. GRAV.": 782.00,
    "MASTER LASSER 3.0mm BLANCO F.V. GRAV.": 782.00,
    "MASTER LASSER 3.0mm LISO ARENADO F.P.": 1123.00,
    "MASTER LASSER 4.0mm LISO ARENADO F.POL": 1246.00,
    "Rollo Prefabricado F.V. 3.5mm (Rojo)": 856.00,
    "MASTER LASSER 3.5mm BLANCO F.V. GRAV.": 856.00,
    "MASTER LASSER 3.5mm ROJO F.P. GRAV.": 1068.00,
    "MASTER LASSER 3.5mm BLANCO F.P. GRAV.": 1068.00,
    "Rollo Prefabricado F.P. 4.0mm (Rojo)": 1226.00,
    "MASTER LASSER 4.0mm BLANCO F.P. GRAV.": 1226.00,
    "Rollo Prefabricado APP 4.5mm (Rojo)": 1375.00,
    "MASTER LASSER 4.5mm BLANCO F.P. GRAV.": 1375.00
}

st.title("🍊 Cotizador Grupo IMAC")
st.write("Sistema Comercial - Plataforma Web")

# Formulario
with st.form("cotizador_form"):
    st.write("### Datos del Cliente")
    vendedor = st.text_input("Tu Nombre (Asesor)")
    cliente = st.text_input("Nombre del Cliente / Proyecto")
    col1, col2 = st.columns(2)
    with col1:
        telefono = st.text_input("Teléfono")
    with col2:
        ciudad = st.text_input("Ciudad / Ubicación")

    st.write("---")
    st.write("### Especificaciones")
    modo = st.radio("Modo de cálculo:", ["Por m²", "Por Cantidad de Rollos"], horizontal=True)
    cantidad = st.number_input("Ingresa el valor:", min_value=0.0, step=1.0)
    producto_nombre = st.selectbox("Selecciona el producto:", list(catalogo_rollos.keys()))
    
    col3, col4 = st.columns(2)
    with col3:
        primario = st.radio("Primario:", ["Base Agua ($725)", "Base Solvente ($1,218)"])
    with col4:
        flete = st.number_input("Costo de Flete ($):", min_value=0.0, step=100.0)

    submit = st.form_submit_button("GENERAR COTIZACIÓN")

if submit:
    if cantidad <= 0 or not cliente or not vendedor:
        st.warning("⚠️ Por favor llena los datos del vendedor, cliente y una cantidad válida.")
    else:
        with st.spinner("Calculando y guardando en la nube..."):
            # Matemáticas
            if modo == "Por m²":
                m2 = cantidad
                rollos = math.ceil((m2 * 1.16) / 10)
            else:
                rollos = math.ceil(cantidad)
                m2 = round((rollos * 10) / 1.16, 2)

            precio_base = catalogo_rollos[producto_nombre]
            flete_unitario = flete / rollos if rollos > 0 else 0
            precio_con_flete = precio_base + flete_unitario
            total_rollos = rollos * precio_con_flete

            cubetas = math.ceil((m2 / 4) / 19)
            precio_primario = 725.0 if "Agua" in primario else 1218.0
            total_primario = cubetas * precio_primario

            subtotal = total_rollos + total_primario
            iva = subtotal * 0.16
            gran_total = subtotal + iva

            # Conectar a Sheets y Guardar
            hoja = conectar_sheets()
            if hoja:
                fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                fila = [fecha_hoy, vendedor, cliente, telefono, ciudad, round(gran_total, 2), "Generado en Web"]
                hoja.append_row(fila)
                st.success(f"✅ ¡Venta registrada exitosamente! Total: ${gran_total:,.2f} MXN")

                # Generar PDF (Básico para Web)
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.set_text_color(255, 102, 0)
                pdf.cell(0, 10, txt="GRUPO IMAC - COTIZACION", ln=True, align='C')
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, txt=f"Cliente: {cliente}", ln=True)
                pdf.cell(0, 10, txt=f"Area aprox: {m2} m2", ln=True)
                pdf.cell(0, 10, txt=f"Producto: {producto_nombre} ({rollos} rollos)", ln=True)
                pdf.cell(0, 10, txt=f"Primario: {cubetas} cubetas", ln=True)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, txt=f"TOTAL: ${gran_total:,.2f} MXN", ln=True)
                
                # Botón de Descarga
                archivo_pdf = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="📥 Descargar PDF", data=archivo_pdf, file_name=f"Cotizacion_{cliente}.pdf", mime="application/pdf")
