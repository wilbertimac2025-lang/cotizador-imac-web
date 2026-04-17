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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador Corporativo IMAC", page_icon="🍊", layout="centered")

# --- CLASE PARA EL PDF PROFESIONAL ---
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Grupo IMAC | Veracruz, Ver. | Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 102, 0)
        self.cell(0, 10, f"{num}. {label}", ln=True, fill=False)
        self.ln(2)

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_sheets():
    try:
        credenciales_dic = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credenciales_dic, scopes=scopes)
        cliente = gspread.authorize(creds)
        # ⚠️ AQUÍ PON EL ID DE TU EXCEL DE VENTAS
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
        msg['Subject'] = f'Cotización Formal de Materiales - Grupo IMAC'
        msg['From'] = remitente
        msg['To'] = destinatario
        
        cuerpo_mensaje = f"""
        Estimado(a) {nombre_cliente},
        
        Adjunto a este correo encontrará la cotización formal de sus materiales impermeabilizantes Master Lasser solicitada a Grupo IMAC.
        
        Quedamos a su entera disposición para cualquier duda o aclaración.
        
        Atentamente,
        El equipo de Grupo IMAC.
        """
        msg.set_content(cuerpo_mensaje)
        msg.add_attachment(archivo_pdf, maintype='application', subtype='pdf', filename=f"Cotizacion_IMAC_{nombre_cliente}.pdf")
        
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.starttls()
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"No se pudo enviar el correo. Error técnico: {e}")
        return False

# --- CATÁLOGO COMPLETO ---
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

# --- ESTILO DE BOTONES ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #FF6600; color: white; height: 3em; width: 100%; border-radius: 10px; font-size: 20px; font-weight: bold;
    }
    .whatsapp-btn {
        background-color: #25D366; color: white; padding: 12px; text-align: center; border-radius: 10px; 
        font-weight: bold; font-size: 18px; margin-bottom: 15px; text-decoration: none; display: block;
    }
    .whatsapp-btn:hover {
        background-color: #1DA851; color: white; text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFAZ WEB ---
st.title("🍊 Cotizador Grupo IMAC")
st.subheader("Sistema de Ventas - Master Lasser")

with st.form("cotizador_form"):
    st.write("### Datos del Cliente")
    vendedor = st.text_input("Tu Nombre (Asesor)")
    cliente = st.text_input("Nombre del Cliente / Proyecto")
    
    col1, col2 = st.columns(2)
    with col1:
        telefono = st.text_input("Teléfono (10 dígitos)")
    with col2:
        ciudad = st.text_input("Ciudad / Ubicación")
        
    correo_destino = st.text_input("Correo electrónico del cliente (Opcional)")

    st.write("---")
    st.write("### Especificaciones de Material")
    modo = st.radio("Modo de cálculo:", ["Por m²", "Por Cantidad de Rollos"], horizontal=True)
    cantidad = st.number_input("Ingresa el valor:", min_value=0.0, step=1.0)
    producto_nombre = st.selectbox("Selecciona el producto:", list(catalogo_rollos.keys()))
    
    col3, col4 = st.columns(2)
    with col3:
        primario = st.radio("Tipo de Primario:", ["Base Agua ($725)", "Base Solvente ($1,218)"])
    with col4:
        flete = st.number_input("Costo de Flete Total ($):", min_value=0.0, step=100.0)

    submit = st.form_submit_button("GENERAR COTIZACIÓN")

if submit:
    if cantidad <= 0 or not cliente or not vendedor:
        st.warning("⚠️ Completa los datos para generar el presupuesto.")
    else:
        with st.spinner("Procesando cotización..."):
            if modo == "Por m²":
                rollos = math.ceil((cantidad * 1.16) / 10)
                etiqueta_area = f"Area total a cubrir: {cantidad} m2"
            else:
                rollos = math.ceil(cantidad)
                m2_aprox = round((rollos * 10) / 1.16, 2)
                etiqueta_area = f"Area aprox. a cubrir: {m2_aprox} m2"

            producto_elegido = catalogo_rollos[producto_nombre]
            flete_u = flete / rollos if rollos > 0 else 0
            precio_final_u = producto_elegido["precio"] + flete_u
            total_rollos = rollos * precio_final_u

            subtotal = total_rollos 
            iva = subtotal * 0.16
            gran_total = subtotal + iva

            # 1. Guardar en Excel
            hoja = conectar_sheets()
            if hoja:
                fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                hoja.append_row([fecha_hoy, vendedor, cliente, ciudad, round(gran_total, 2)])
                
                # 2. Generar PDF
                pdf = PDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.set_text_color(255, 102, 0)
                pdf.cell(0, 10, "GRUPO IMAC", ln=True, align='R')
                pdf.set_font("Arial", size=10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, "Cotizacion Formal de Materiales", ln=True, align='R')
                pdf.ln(10)

                pdf.set_fill_color(255, 102, 0)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"  CLIENTE: {cliente}", ln=True, fill=True)
                pdf.ln(5)

                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 8, f"Producto: {producto_nombre}", ln=True)
                pdf.cell(0, 8, f"Cantidad: {rollos} rollos", ln=True)
                pdf.cell(0, 8, f"Ubicacion: {ciudad}", ln=True)
                pdf.cell(0, 8, etiqueta_area, ln=True)
                
                pdf.ln(5)
                pdf.set_font("Courier", 'B', 12)
                pdf.cell(0, 10, f"Precio unitario: ${precio_final_u:,.2f} MXN", ln=True, align='R')
                pdf.set_font("Courier", 'B', 14)
                pdf.set_text_color(255, 102, 0)
                pdf.cell(0, 10, f"TOTAL A PAGAR: ${gran_total:,.2f} MXN", ln=True, align='R', fill=False)

                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.success("✅ Cotización registrada exitosamente.")
                
                # 3. Botón de Descarga Manual
                st.download_button(label="📥 Descargar PDF de Cotización", data=pdf_output, file_name=f"Cotizacion_IMAC_{cliente}.pdf")
                
                # 4. Enviar Correo (Si hay)
                if correo_destino:
                    with st.spinner("Enviando correo..."):
                        if enviar_correo(correo_destino, pdf_output, cliente):
                            st.success(f"📧 ¡Enviado a {correo_destino}!")
                
                # 5. Generar enlace de WhatsApp (Si hay teléfono)
                if telefono:
                    numero_limpio = telefono.replace(" ", "").replace("-", "")
                    if not numero_limpio.startswith("+52") and len(numero_limpio) == 10:
                        numero_limpio = "+52" + numero_limpio
                    
                    mensaje = f"Hola {cliente}, te comparto tu cotización formal por los materiales de impermeabilización Master Lasser solicitados a Grupo IMAC. Quedo a tus órdenes."
                    mensaje_codificado = urllib.parse.quote(mensaje)
                    link_whatsapp = f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_codificado}"
                    
                    st.markdown(f"""
                        <a href="{link_whatsapp}" target="_blank" class="whatsapp-btn">
                            💬 Enviar mensaje por WhatsApp
                        </a>
                        """, unsafe_allow_html=True)
