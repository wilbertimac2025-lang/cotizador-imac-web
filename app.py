import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import math
from fpdf import FPDF
import datetime
import json
import smtplib
from email.message import EmailMessage
import urllib.parse
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador Corporativo IMAC", page_icon="🍊", layout="centered")

# --- CLASE PARA EL PDF PROFESIONAL (DISEÑO RESTAURADO) ---
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
        # ⚠️ REEMPLAZA CON TU ID DE EXCEL
        sheet = cliente.open_by_key("1-ns2kgub6g4Mg0gQOr-X1ngodUFMWyrbhf9TEUv1T6c").sheet1
        return sheet
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- FUNCIÓN PARA ENVIAR CORREO (MICROSOFT 365) ---
def enviar_correo(destinatario, archivo_pdf, nombre_cliente):
    try:
        remitente = st.secrets["CORREO_BOT"]
        password = st.secrets["PASS_BOT"]
        msg = EmailMessage()
        msg['Subject'] = f'Cotización Formal - Grupo IMAC ({nombre_cliente})'
        msg['From'] = remitente
        msg['To'] = destinatario
        msg.set_content(f"Estimado(a) {nombre_cliente},\n\nAdjuntamos la cotización formal de Master Lasser solicitada.\n\nAtentamente,\nGrupo IMAC.")
        msg.add_attachment(archivo_pdf, maintype='application', subtype='pdf', filename=f"Cotizacion_IMAC_{nombre_cliente}.pdf")
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.starttls()
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except: return False

# --- CATÁLOGO ---
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

# --- ESTILOS ---
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #FF6600; color: white; height: 3em; width: 100%; border-radius: 10px; font-weight: bold; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 12px; text-align: center; border-radius: 10px; font-weight: bold; text-decoration: none; display: block; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍊 Cotizador Grupo IMAC")

with st.form("cotizador_form"):
    vendedor = st.text_input("Asesor Comercial")
    cliente = st.text_input("Nombre del Cliente")
    col1, col2 = st.columns(2)
    with col1: tel = st.text_input("Teléfono (10 dígitos)")
    with col2: ciudad = st.text_input("Ubicación")
    correo = st.text_input("Correo del cliente (Opcional)")
    
    modo = st.radio("Cálculo por:", ["m²", "Rollos"], horizontal=True)
    cant = st.number_input("Cantidad:", min_value=0.0)
    prod = st.selectbox("Producto:", list(catalogo_rollos.keys()))
    flete = st.number_input("Flete Total ($):", min_value=0.0)
    
    submit = st.form_submit_button("GENERAR COTIZACIÓN")

if submit:
    if cant <= 0 or not cliente:
        st.error("Datos incompletos.")
    else:
        with st.spinner("Generando formato profesional..."):
            # Cálculos
            rollos = math.ceil((cant * 1.16) / 10) if modo == "m²" else math.ceil(cant)
            p_base = catalogo_rollos[prod]["precio"]
            f_u = flete / rollos if rollos > 0 else 0
            unitario = p_base + f_u
            subtotal = rollos * unitario
            iva = subtotal * 0.16
            total = subtotal + iva

            # Guardar en Sheets
            hoja = conectar_sheets()
            if hoja:
                hoja.append_row([datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), vendedor, cliente, ciudad, round(total, 2)])

            # PDF RESTAURADO
            pdf = PDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(255, 102, 0)
            pdf.cell(0, 10, "GRUPO IMAC", ln=True, align='R')
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "Cotización Formal de Materiales", ln=True, align='R')
            pdf.ln(10)

            # Cuadro Cliente
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"  DIRIGIDO A: {cliente}", ln=True, fill=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(100, 8, f"  Ubicación: {ciudad}")
            pdf.cell(90, 8, f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
            pdf.ln(5)

            # Detalle
            pdf.set_fill_color(255, 102, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 10, "  DESCRIPCIÓN DEL SUMINISTRO", ln=True, fill=True)
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, txt=f"Suministro de {rollos} rollos de {prod}.\nÁrea aproximada de cobertura: {cant if modo == 'm²' else round((rollos*10)/1.16,2)} m2.")
            
            # Totales
            pdf.ln(5)
            pdf.set_font("Courier", 'B', 12)
            pdf.cell(120, 10, "PRECIO UNITARIO (NETO):")
            pdf.cell(70, 10, f"${unitario:,.2f} MXN", ln=True, align='R')
            pdf.set_font("Courier", 'B', 14)
            pdf.set_text_color(255, 102, 0)
            pdf.cell(120, 12, "TOTAL A PAGAR (CON IVA):")
            pdf.cell(70, 12, f"${total:,.2f} MXN", ln=True, align='R')

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.success("✅ Cotización lista.")
            st.download_button("📥 1. DESCARGAR PDF", data=pdf_bytes, file_name=f"Cotizacion_{cliente}.pdf")
            
            if tel:
                msg_wa = urllib.parse.quote(f"Hola {cliente}, te envío la cotización de Grupo IMAC. Favor de adjuntar el PDF que acabas de descargar.")
                link_wa = f"https://api.whatsapp.com/send?phone=52{tel}&text={msg_wa}"
                st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">💬 2. ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
            
            if correo:
                if enviar_correo(correo, pdf_bytes, cliente): st.info("📧 Correo enviado.")
