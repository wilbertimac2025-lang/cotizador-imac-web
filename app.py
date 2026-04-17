import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import math
from fpdf import FPDF
import datetime
import json
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador Corporativo IMAC", page_icon="🍊", layout="centered")

# --- CLASE PARA EL PDF PROFESIONAL ---
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Grupo IMAC | Veracruz, Ver. | Pagina {self.page_no()}', 0, 0, 'C')

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_sheets():
    try:
        credenciales_dic = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credenciales_dic, scopes=scopes)
        cliente = gspread.authorize(creds)
        # ⚠️ REEMPLAZA CON EL ID DE TU EXCEL DE VENTAS
        sheet = cliente.open_by_key("1-ns2kgub6g4Mg0gQOr-X1ngodUFMWyrbhf9TEUv1T6c").sheet1
        return sheet
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- CATÁLOGO DE PRODUCTOS ---
catalogo_rollos = {
    "MASTER LASSER 3.0mm ROJO F.V. GRAV.": {"clave": "IP050701", "precio": 782.00},
    "MASTER LASSER 3.0mm BLANCO F.V. GRAV.": {"clave": "IP050702", "precio": 782.00},
    "MASTER LASSER 3.0mm LISO ARENADO F.P.": {"clave": "IP050704", "precio": 1123.00},
    "MASTER LASSER 4.0mm LISO ARENADO F.POL": {"clave": "IP050706", "precio": 1246.00},
    "Rollo Prefabricado F.V. 3.5mm (Rojo)": {"clave": "IP050709", "precio": 856.00},
    "MASTER LASSER 3.5mm BLANCO F.V. GRAV.": {"clave": "IP050710", "precio": 856.00},
    "MASTER LASSER 3.5mm ROJO F.P. GRAV.": {"clave": "IP050712", "precio": 1068.00},
    "MASTER LASSER 3.5mm BLANCO F.P. GRAV.": {"clave": "IP050713", "precio": 1068.00},
    "Rollo Prefabricado F.P. 4.0mm (Rojo)": {"clave": "IP050715", "precio": 1226.00},
    "MASTER LASSER 4.0mm BLANCO F.P. GRAV.": {"clave": "IP050716", "precio": 1226.00},
    "Rollo Prefabricado APP 4.5mm (Rojo)": {"clave": "IP050718", "precio": 1375.00},
    "MASTER LASSER 4.5mm BLANCO F.P. GRAV.": {"clave": "IP050719", "precio": 1375.00}
}

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #FF6600; color: white; height: 3em; width: 100%; border-radius: 10px; font-size: 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🍊 Cotizador Grupo IMAC")
st.subheader("Sistema de Ventas - Master Lasser")

with st.form("cotizador_form"):
    st.write("### Datos del Cliente")
    vendedor = st.text_input("Asesor Comercial")
    cliente = st.text_input("Nombre del Cliente / Proyecto")
    col1, col2 = st.columns(2)
    with col1:
        telefono = st.text_input("Teléfono")
    with col2:
        ciudad = st.text_input("Ciudad / Ubicación")

    st.write("---")
    st.write("### Especificaciones")
    modo = st.radio("Cálculo por:", ["m²", "Cantidad de Rollos"], horizontal=True)
    cantidad = st.number_input("Valor:", min_value=0.0, step=1.0)
    producto_nombre = st.selectbox("Selecciona Producto:", list(catalogo_rollos.keys()))
    
    col3, col4 = st.columns(2)
    with col3:
        primario = st.radio("Primario:", ["Base Agua ($725)", "Base Solvente ($1,218)"])
    with col4:
        flete = st.number_input("Costo de Flete Total ($):", min_value=0.0)

    submit = st.form_submit_button("GENERAR COTIZACIÓN")

if submit:
    if cantidad <= 0 or not cliente:
        st.warning("⚠️ Ingresa los m2/rollos y nombre del cliente.")
    else:
        with st.spinner("Preparando formato oficial..."):
            # Lógica de cálculo
            rollos = math.ceil((cantidad * 1.16) / 10) if modo == "m²" else math.ceil(cantidad)
            area_m2 = cantidad if modo == "m²" else round((rollos * 10) / 1.16, 2)
            
            p_base = catalogo_rollos[producto_nombre]["precio"]
            f_u = flete / rollos if rollos > 0 else 0
            unitario = p_base + f_u
            subtotal = rollos * unitario
            iva = subtotal * 0.16
            total = subtotal + iva

            # Registro en Google Sheets
            hoja = conectar_sheets()
            if hoja:
                hoja.append_row([datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), vendedor, cliente, ciudad, round(total, 2)])

            # Construcción del PDF
            pdf = PDF()
            pdf.add_page()
            
            # Intento de cargar logo si existe en el repo
            try:
                if os.path.exists("logo.jpg"): pdf.image("logo.jpg", x=10, y=8, w=45)
            except: pass

            # Encabezado Corporativo
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(255, 102, 0)
            pdf.cell(0, 10, "GRUPO IMAC", ln=True, align='R')
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "Suministro de Impermeabilizantes", ln=True, align='R')
            pdf.ln(15)

            # Sección Cliente
            pdf.set_fill_color(240, 240, 240)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"  COTIZACIÓN PARA: {cliente.upper()}", ln=True, fill=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(100, 8, f"  Ubicación: {ciudad}")
            pdf.cell(90, 8, f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
            pdf.ln(5)

            # Detalle Técnico
            pdf.set_fill_color(255, 102, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "  DESCRIPCIÓN DEL MATERIAL", ln=True, fill=True)
            pdf.ln(3)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 7, txt=f"Suministro de {rollos} unidades de {producto_nombre}.\n"
                                     f"Área estimada de cobertura: {area_m2} m2.")
            pdf.ln(5)

            # Tabla de Costos
            pdf.set_font("Courier", 'B', 12)
            pdf.cell(120, 10, "PRECIO UNITARIO:")
            pdf.cell(70, 10, f"${unitario:,.2f} MXN", ln=True, align='R')
            
            pdf.ln(2)
            pdf.set_font("Courier", 'B', 14)
            pdf.set_text_color(255, 102, 0)
            pdf.cell(120, 12, "TOTAL NETO (CON IVA):", border='T')
            pdf.cell(70, 12, f"${total:,.2f} MXN", border='T', ln=True, align='R')

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.success("✅ Cotización generada correctamente.")
            st.download_button("📥 DESCARGAR COTIZACIÓN PDF", data=pdf_bytes, file_name=f"Cotizacion_IMAC_{cliente}.pdf")
