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
        # ⚠️ AQUÍ DEBE IR TU ID REAL DE GOOGLE SHEETS (EJEMPLO: "1AbC...XYZ")
        sheet = cliente.open_by_key("1-ns2kgub6g4Mg0gQOr-X1ngodUFMWyrbhf9TEUv1T6c").sheet1
        return sheet
    except Exception as e:
        st.error("Error conectando a la base de datos. Verifica los secretos.")
        return None

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
    </style>
    """, unsafe_allow_html=True)

# --- INTERFAZ WEB ---
st.title("🍊 Cotizador Grupo IMAC")
st.subheader("Sistema Móvil - Plataforma Web")

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

# --- LÓGICA DE GENERACIÓN ---
if submit:
    if cantidad <= 0 or not cliente or not vendedor:
        st.warning("⚠️ Por favor llena los datos del vendedor, cliente y una cantidad válida.")
    else:
        with st.spinner("Generando PDF profesional y guardando en la nube..."):
            # Cálculos
            if modo == "Por m²":
                m2 = cantidad
                rollos = math.ceil((m2 * 1.16) / 10)
                etiqueta_area = f"Area total a cubrir: {m2} m2"
            else:
                rollos = math.ceil(cantidad)
                m2 = round((rollos * 10) / 1.16, 2)
                etiqueta_area = f"Area aprox. a cubrir: {m2} m2"

            producto_elegido = catalogo_rollos[producto_nombre]
            precio_base = producto_elegido["precio"]
            flete_unitario = flete / rollos if rollos > 0 else 0
            precio_con_flete = precio_base + flete_unitario
            total_rollos = rollos * precio_con_flete

            cubetas = math.ceil((m2 / 4) / 19)
            precio_primario = 725.0 if "Agua" in primario else 1218.0
            nombre_primario = 'MASTER PRIM "A" CUB. 19 LTS.' if "Agua" in primario else 'MASTER PRIM "S" CUB. 19 LTS.'
            total_primario = cubetas * precio_primario

            subtotal = total_rollos + total_primario
            iva = subtotal * 0.16
            gran_total = subtotal + iva

            # 1. Guardar en Google Sheets
            hoja = conectar_sheets()
            if hoja:
                fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                fila = [fecha_hoy, vendedor, cliente, telefono, ciudad, round(gran_total, 2), "Generado en Web"]
                hoja.append_row(fila)
                st.success(f"✅ ¡Venta registrada exitosamente! Total: ${gran_total:,.2f} MXN")

                # 2. Generar PDF
                pdf = PDF()
                pdf.add_page()
                
                # Logo grande
                try:
                    if os.path.exists("logo.jpg"):
                        pdf.image("logo.jpg", x=10, y=8, w=60)
                    elif os.path.exists("logo.png"):
                        pdf.image("logo.png", x=10, y=8, w=60)
                except:
                    pass

                # Encabezado
                pdf.set_font("Arial", 'B', 16)
                pdf.set_text_color(255, 102, 0)
                pdf.cell(0, 8, txt="GRUPO IMAC", ln=True, align='R')
                pdf.set_font("Arial", size=10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, txt="Soluciones en Impermeabilizacion", ln=True, align='R')
                pdf.cell(0, 5, txt="Tel: (229) 935-06-94 Ext. 23", ln=True, align='R')
                pdf.cell(0, 5, txt="masterventas@grupo-imac.com", ln=True, align='R')
                pdf.ln(10)

                # Título Naranja
                pdf.set_fill_color(255, 102, 0)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, txt="  COTIZACION FORMAL", ln=True, fill=True)
                pdf.ln(5)

                # Datos del Cliente
                pdf.set_text_color(0, 0, 0)
                fecha_pdf = datetime.datetime.now().strftime("%d/%m/%Y")
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(100, 6, txt=f"Cliente / Proyecto: {cliente}")
                pdf.set_font("Arial", size=11)
                pdf.cell(90, 6, txt=f"Fecha de emision: {fecha_pdf}", ln=True, align='R')
                pdf.set_font("Arial", size=10)
                pdf.cell(100, 6, txt=f"Ubicacion: {ciudad}")
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(90, 6, txt=etiqueta_area, ln=True, align='R')
                pdf.ln(5)

                # SECCIÓN 1
                pdf.chapter_title(1, "SISTEMA IMPERMEABILIZANTE")
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 6, txt=f"Clave: {producto_elegido['clave']}", ln=True)
                pdf.cell(0, 6, txt=f"Producto: {producto_nombre}", ln=True)
                texto_cantidad_rollos = f"Cantidad: {rollos} rollos (Incluye mermas)" if modo == "Por m²" else f"Cantidad: {rollos} rollos (Piezas directas)"
                pdf.cell(0, 6, txt=texto_cantidad_rollos, ln=True)
                
                pdf.set_font("Courier", size=11)
                txt_precio_u = f"Precio unitario (C/Flete): ${precio_con_flete:,.2f} MXN"
                pdf.cell(0, 6, txt=txt_precio_u.rjust(60), ln=True, align='R')
                
                pdf.set_font("Arial", 'B', 11)
                txt_importe_r = f"Importe Seccion Rollos: ${total_rollos:,.2f} MXN"
                pdf.cell(0, 6, txt=txt_importe_r.rjust(60), ln=True, align='R')
                pdf.ln(5)

                # SECCIÓN 2
                pdf.chapter_title(2, "MATERIAL DE PREPARACION")
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 6, txt=f"Producto: {nombre_primario}", ln=True)
                pdf.cell(0, 6, txt=f"Cantidad: {cubetas} cubeta(s) de 19L (Rend. 4m2/L)", ln=True)
                
                pdf.set_font("Arial", 'B', 11)
                txt_importe_p = f"Importe Seccion Primario: ${total_primario:,.2f} MXN"
                pdf.cell(0, 6, txt=txt_importe_p.rjust(60), ln=True, align='R')
                pdf.ln(8)

                # TOTALES CUADRADOS
                pdf.set_font("Courier", size=12)
                pdf.set_fill_color(240, 240, 240)
                col1 = 120
                col2 = 70
                
                pdf.cell(col1, 8, txt="")
                pdf.cell(col2, 8, txt=f"SUBTOTAL: ${subtotal:,.2f}".rjust(20), ln=True, align='R', fill=True)
                
                pdf.cell(col1, 8, txt="")
                pdf.cell(col2, 8, txt=f"I.V.A. (16%): ${iva:,.2f}".rjust(20), ln=True, align='R', fill=True)
                
                pdf.set_font("Courier", 'B', 14)
                pdf.set_text_color(255, 102, 0)
                pdf.cell(col1, 10, txt="")
                pdf.cell(col2, 10, txt=f"TOTAL: ${gran_total:,.2f}".rjust(20), ln=True, align='R', fill=True)
                pdf.ln(10)

                # TÉRMINOS
                pdf.set_fill_color(255, 102, 0)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 6, txt="  TERMINOS Y CONDICIONES COMERCIALES", ln=True, fill=True)
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("Arial", size=9)
                terminos = (
                    "1. Precios sujetos a cambio sin previo aviso.\n"
                    "2. Vigencia de la cotizacion: 15 dias habiles.\n"
                    "3. Tiempo de entrega: 2 a 3 dias habiles una vez confirmado el anticipo.\n"
                    "4. El material se entrega a pie de obra en planta baja."
                )
                pdf.multi_cell(0, 5, txt=terminos)
                pdf.ln(5)

                # DATOS BANCARIOS E IMÁGENES CORREGIDAS
                pdf.set_fill_color(240, 240, 240)
                pdf.set_text_color(255, 102, 0)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 6, txt="  DATOS PARA DEPOSITO / TRANSFERENCIA", ln=True, fill=True)
                pdf.ln(2)
                
                # Guardar altura para alinear texto e imagen
                y_pos_banco = pdf.get_y()
                
                # Texto Banco a la Izquierda
                pdf.set_font("Courier", size=9)
                pdf.set_text_color(50, 50, 50)
                banco_txt = (
                    "Banco: BBVA\n"
                    "Cuenta: 0134508394\n"
                    "CLABE: 012905001345083942\n"
                    "RFC: IVE840928BS5"
                )
                pdf.multi_cell(90, 5, txt=banco_txt)
                
                # Imagen Banco a la Derecha (Más pequeña)
                try:
                    if os.path.exists("banco.png") or os.path.exists("banco.jpg"):
                        ruta_banco = "banco.png" if os.path.exists("banco.png") else "banco.jpg"
                        pdf.image(ruta_banco, x=130, y=y_pos_banco, w=35)
                except:
                    pass

                # Asegurar espacio antes de marcas
                pdf.set_y(y_pos_banco + 25)

                # Marcas Finales (Centradas y más chicas)
                try:
                    if os.path.exists("logos_marcas.png") or os.path.exists("logos_marcas.jpg"):
                        ruta_marcas = "logos_marcas.png" if os.path.exists("logos_marcas.png") else "logos_marcas.jpg"
                        y_marcas = pdf.get_y()
                        pdf.image(ruta_marcas, x=40, y=y_marcas, w=130)
                except:
                    pass

                # Botón Descarga
                archivo_pdf = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="📥 Descargar PDF Formal", data=archivo_pdf, file_name=f"Cotizacion_IMAC_{cliente}.pdf", mime="application/pdf")
