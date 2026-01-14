from tkinter import *
from tkinter import messagebox
import os
import cv2
import sys
from matplotlib import pyplot as plt
from mtcnn.mtcnn import MTCNN
import numpy as np
from datetime import datetime, time
from PIL import Image, ImageTk
import mysql.connector
from dotenv import load_dotenv
from deepface import DeepFace
import hashlib  # Para encriptar contraseñas
# Cargar variables de entorno
load_dotenv()

class SistemaAsistencia:
    def __init__(self):
        self.pantalla = Tk()
        self.camara_lista = False
        # 📌 Ruta base (donde está el exe)
        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            
        # 📁 Directorio principal
        self.APP_DIR = BASE_DIR  # C:\Reconocimiento_facial
        
        # 📂 Subcarpetas
        self.IMG_DIR = os.path.join(self.APP_DIR, "img")
        self.REGISTRO_DIR = os.path.join(self.APP_DIR, "rostros_registro")
        self.ASISTENCIA_DIR = os.path.join(self.APP_DIR, "rostros_asistencia")
        self.LOG_DIR = os.path.join(self.APP_DIR, "logs")
        
        # Crear carpetas
        os.makedirs(self.REGISTRO_DIR, exist_ok=True)
        os.makedirs(self.ASISTENCIA_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)
        os.makedirs(self.IMG_DIR, exist_ok=True)
        # 🔐 Cargar .env
        env_path = os.path.join(self.APP_DIR, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            print("⚠️ Archivo .env no encontrado")
        # Configuración de base de datos
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        
        self.crear_pantalla_principal()

    def conectar_db(self):
        """Establece conexión con la base de datos"""
        try:
            conexion = mysql.connector.connect(**self.db_config)
            return conexion
        except mysql.connector.Error as err:
            messagebox.showerror("Error de BD", f"Error al conectar a la base de datos:\n{err}")
            return None
    
    def centrar_ventana(self, ventana, ancho, alto, resizable=False):
        ventana.update_idletasks()  # Evita centrar mal en algunos sistemas

        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()

        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)

        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana.resizable(resizable, resizable)

    def encriptar_password(self, password):
        """
        Encripta una contraseña usando SHA256
        
        Args:
            password (str): Contraseña en texto plano
            
        Returns:
            str: Hash SHA256 de 64 caracteres hexadecimales
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def login_administrador(self):
        """
        Ventana de login para validar administrador ANTES del registro
        """
        # ───────────────────────────────────────────────────────────
        # 🎨 CREAR VENTANA
        # ───────────────────────────────────────────────────────────
        ventana_login = Toplevel(self.pantalla)
        ventana_login.title("🔒 Acceso de Administrador")
        
        
      
        ventana_login.configure(bg="#eceff1")
        self.centrar_ventana(ventana_login, 420, 420)
        
        # Modal (bloquear ventana principal)
        ventana_login.transient(self.pantalla)
        ventana_login.grab_set()
        
        # ───────────────────────────────────────────────────────────
        # 🎨 HEADER
        # ───────────────────────────────────────────────────ñ────────
        header = Frame(ventana_login, bg="#37474f", height=90)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        Label(header, text="🔐", bg="#37474f", 
            font=("Segoe UI Emoji", 20)).pack(pady=(5, 0))
        
        Label(header, text="ACCESO DE ADMINISTRADOR", 
            bg="#37474f", fg="white", 
            font=("Arial", 13, "bold")).pack()
        
        # ───────────────────────────────────────────────────────────
        # 📝 FORMULARIO
        # ───────────────────────────────────────────────────────────
        form_frame = Frame(ventana_login, bg="#eceff1")
        form_frame.pack(pady=30, padx=40, fill='both', expand=True)
        
        # Campo Usuario
        Label(form_frame, text="👤 Usuario Administrador:", 
            bg="#eceff1", fg="#37474f", 
            font=("Arial", 10, "bold")).pack(anchor='w', pady=(10, 5))
        
        entry_usuario = Entry(form_frame, font=("Arial", 11), bd=2, 
                            relief='solid', bg="white")
        entry_usuario.pack(fill='x', ipady=10)
        entry_usuario.focus()
        
        # Campo Contraseña
        Label(form_frame, text="🔑 Contraseña:", 
            bg="#eceff1", fg="#37474f", 
            font=("Arial", 10, "bold")).pack(anchor='w', pady=(20, 5))
        
        entry_password = Entry(form_frame, font=("Arial", 11), bd=2, 
                            relief='solid', show="●", bg="white")
        entry_password.pack(fill='x', ipady=10)
        
        # Mensaje de error (oculto inicialmente)
        label_error = Label(form_frame, text="", bg="#eceff1", 
                        fg="#f44336", font=("Arial", 9, "bold"))
        label_error.pack(pady=(15, 0))
        
        # ───────────────────────────────────────────────────────────
        #  VALIDACIÓN CON HASH
        # ───────────────────────────────────────────────────────────
        def validar_login():
            usuario = entry_usuario.get().strip()
            password = entry_password.get().strip()
            
            # Validar campos vacíos
            if not usuario or not password:
                label_error.config(text="⚠️ Complete todos los campos")
                return
            
            # ENCRIPTAR CONTRASEÑA INGRESADA
            #password_hash = self.encriptar_password(password)
            
            # Validar contra base de datos
            conexion = self.conectar_db()
            if conexion:
                try:
                    cursor = conexion.cursor()
                    
                    # 🔥 QUERY: Comparar con hash almacenado
                    query = """
                        SELECT id, nombre, rol 
                        FROM administradores 
                        WHERE usuario = %s AND password = %s AND activo = 1
                    """
                    cursor.execute(query, (usuario,password))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        # ✅ LOGIN EXITOSO
                        admin_id, admin_nombre, admin_rol = resultado
                        
                        # Registrar último acceso
                        cursor.execute(
                            "UPDATE administradores SET ultimo_acceso = NOW() WHERE id = %s",
                            (admin_id,)
                        )
                        conexion.commit()
                        
                        cursor.close()
                        conexion.close()
                        
                        ventana_login.destroy()
                        
                        messagebox.showinfo(
                            "✅ Acceso Concedido",
                            f"Bienvenido(a) {admin_nombre}\n"
                            f"Rol: {admin_rol}\n\n"
                            f"Ahora puede registrar usuarios"
                        )
                        
                        # Abrir ventana de registro
                        self.ventana_registro()
                        
                    else:
                        # ❌ CREDENCIALES INCORRECTAS
                        label_error.config(text="❌ Usuario o contraseña incorrectos")
                        entry_password.delete(0, END)
                        entry_password.focus()
                        
                except Exception as e:
                    messagebox.showerror("Error BD", f"Error al validar:\n{str(e)}")
                    if conexion and conexion.is_connected():
                        conexion.close()
            else:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
        
        # ───────────────────────────────────────────────────────────
        # 🔘 BOTONES
        # ───────────────────────────────────────────────────────────
        buttons_frame = Frame(form_frame, bg="#eceff1")
        buttons_frame.pack(pady=(25, 0))
        
        # Botón Ingresar
        Button(
            buttons_frame,
            text="🔓  Ingresar",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            width=12,
            bd=0,
            cursor="hand2",
            padx=15,
            pady=10,
            command=validar_login
        ).pack(side='left', padx=8)
        
        # Botón Cancelar
        Button(
            buttons_frame,
            text="❌  Cancelar",
            bg="#f44336",
            fg="white",
            font=("Arial", 11, "bold"),
            width=12,
            bd=0,
            cursor="hand2",
            padx=15,
            pady=10,
            command=ventana_login.destroy
        ).pack(side='left', padx=8)
        
        # ───────────────────────────────────────────────────────────
        # ⌨️ ATAJOS DE TECLADO
        # ───────────────────────────────────────────────────────────
        entry_password.bind("<Return>", lambda e: validar_login())
        ventana_login.bind("<Escape>", lambda e: ventana_login.destroy())
        
    def crear_pantalla_principal(self):
        """Crea y configura la pantalla principal del sistema."""
        
        # Configuración inicial de la ventana
        self.pantalla.title("Sistema de Control de Asistencia")
        self.centrar_ventana(self.pantalla, 400, 400)

        # =========================
        # CANVAS (FONDO)
        # =========================
        canvas = Canvas(
            self.pantalla, 
            width=400, 
            height=400, 
            highlightthickness=0
        )
        canvas.place(x=0, y=0)

        # Cargar y redimensionar imagen de fondo
        ruta_img = os.path.join(self.IMG_DIR, "prueb1.jpg")
        img = Image.open(ruta_img)
        img = img.resize((400, 400), Image.LANCZOS)
        
        self.bg_img = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        # =========================
        # HEADER
        # =========================
        canvas.create_rectangle(
            0, 0, 400, 60,
            fill="black",
            stipple="gray50",  # Simula transparencia
            outline=""
        )
        canvas.create_text(
            200, 30,
            text="CONTROL DE ASISTENCIA",
            fill="white",
            font=("Verdana", 14, "bold")
        )

        # =========================
        # BOTONES
        # =========================
        
        # Configuración común de botones
        config_boton = {
            "width": 30,
            "height": 2,
            "font": ("Arial", 11, "bold")
        }
        
        # Botón Registro
        Button(
            self.pantalla,
            text="👤 Registro de Usuario",
            bg="#2196F3",
            fg="white",
            command=self.login_administrador,  # Login primero
            **config_boton
        ).place(relx=0.5, y=150, anchor="center")

        # Botón Asistencia
        Button(
            self.pantalla,
            text="📋 Marcar Asistencia",
            bg="#4CAF50",
            fg="white",
            command=self.ventana_marcar_asistencia,
            **config_boton
        ).place(relx=0.5, y=230, anchor="center")

        # Botón Salir
        Button(
            self.pantalla,
            text="❌ Salir",
            bg="#f44336",
            fg="white",
            command=self.pantalla.quit,
            **config_boton
        ).place(relx=0.5, y=310, anchor="center")
    
    def ventana_registro(self):
        """Crea la ventana de registro de nuevo usuario."""
        
        # Configuración de la ventana
        self.pantalla_registro = Toplevel(self.pantalla)
        self.pantalla_registro.title("Registro de Usuario")
        self.centrar_ventana(self.pantalla_registro, 350, 350)

        # =========================
        # HEADER
        # =========================
        Label(
            self.pantalla_registro,
            text="REGISTRO DE NUEVO USUARIO",
            bg="#3500C5",
            fg="white",
            width=300,
            height=2,
            font=("Arial", 12, "bold")
        ).pack()

        # Espaciador
        Label(self.pantalla_registro, text="").pack(pady=10)

        # =========================
        # CAMPO DE USUARIO
        # =========================
        Label(
            self.pantalla_registro,
            text="Ingrese nombre de usuario:",
            font=("Arial", 11, "bold")
        ).pack()

        self.usuario_registro = StringVar()
        entry_usuario = Entry(
            self.pantalla_registro,
            textvariable=self.usuario_registro,
            font=("Arial", 14),
            width=25,
            justify="center"
        )
        entry_usuario.pack(pady=10)
        entry_usuario.focus()

        # Espaciador
        Label(self.pantalla_registro, text="").pack(pady=5)

        # =========================
        # BOTÓN SIGUIENTE
        # =========================
        Button(
            self.pantalla_registro,
            text="➡️ SIGUIENTE",
            width=25,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.preparar_captura_registro
        ).pack(pady=10)

        # =========================
        # LABEL RESULTADO
        # =========================
        self.label_resultado_reg = Label(
            self.pantalla_registro,
            text="",
            font=("Arial", 10)
        )
        self.label_resultado_reg.pack()
    
    def preparar_captura_registro(self):
        usuario = self.usuario_registro.get().strip()
        
        if not usuario:
            messagebox.showerror("Error", "Debe ingresar un nombre de usuario")
            return
        
        if len(usuario) < 3:
            messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres")
            return
        
        # Verificar si el usuario ya existe en BD
        conexion = self.conectar_db()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = %s", (usuario,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Advertencia", "Este usuario ya está registrado")
                    cursor.close()
                    conexion.close()
                    return
                cursor.close()
                conexion.close()
            except mysql.connector.Error as err:
                messagebox.showerror("Error de BD", f"Error al verificar usuario:\n{err}")
                conexion.close()
                return
        
        # Cerrar ventana de registro y abrir ventana de captura
        self.pantalla_registro.destroy()
        self.ventana_captura_registro(usuario)

    def ventana_captura_registro(self, usuario):
        """Crea la ventana de preparación para captura de rostro."""
        
        # Configuración de la ventana
        self.pantalla_captura = Toplevel(self.pantalla)
        self.pantalla_captura.title("Captura de Rostro - Registro")
        self.centrar_ventana(self.pantalla_captura, 400, 400)

        # =========================
        # HEADER
        # =========================
        Label(
            self.pantalla_captura,
            text="PREPARACIÓN PARA CAPTURA",
            bg="#3500C5",
            fg="white",
            width=400,
            height=2,
            font=("Arial", 12, "bold")
        ).pack()

        # Espaciador
        Label(self.pantalla_captura, text="").pack(pady=5)

        # Instrucciones
        frame_instrucciones = Frame(
            self.pantalla_captura,
            bg="#FFF3E0",
            relief=RIDGE,
            borderwidth=3
        )
        frame_instrucciones.pack(pady=10, padx=20, fill=BOTH)

        Label(
            frame_instrucciones,
            text="📸 INSTRUCCIONES IMPORTANTES:",
            font=("Arial", 11, "bold"),
            bg="#FFE8C4",
            fg="#F0A400"
        ).pack(pady=8)

        # Lista de instrucciones
        instrucciones = [
            "✓ Centra tu rostro, se realizarán 3 capturas",
            "✓ Asegúrate de tener buena iluminación",
            "✓ Retira lentes o accesorios si es posible",
            "✓ Mantén una expresión neutral"
        ]
        for texto in instrucciones:
            Label(
                frame_instrucciones,
                text=texto,
                font=("Arial", 10),
                bg="#FFF3E0",
                anchor="center"
            ).pack(padx=20, pady=3, fill=X)

        # Espaciador
        Label(self.pantalla_captura, text="").pack(pady=2)
        
        Button(
            self.pantalla_captura,
            text=" INICIAR CAPTURA",
            width=30,
            height=2,
            bg="#27B42B",
            fg="white",
            font=("Arial", 10, "bold"),
            command=lambda: self.capturar_rostro_registro(usuario,self.pantalla_captura)
        ).pack(pady=5)

        Button(
            self.pantalla_captura,
            text="Cancelar",
            width=30,
            height=2,
            bg="#f02a1c",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.pantalla_captura.destroy
        ).pack(pady=5)

    def capturar_rostro_registro(self, usuario, pantalla_captura):
        """
        Captura y registra 3 rostros de un usuario.
        Validación solo al momento de capturar (máximo rendimiento).
        """
        try:
            # ═══════════════════════════════════════════════════════════════
            # 📋 CONFIGURACIÓN DE CAPTURAS MÚLTIPLES
            # ═══════════════════════════════════════════════════════════════
            total_capturas = 3
            capturas_realizadas = 0
            imagenes_guardadas = []  # Lista para guardar nombres de archivos
            
            # ══════════════════════════════════════════
            # 🔄 BUCLE DE CAPTURAS (3 veces)
            # ══════════════════════════════════════════
            while capturas_realizadas < total_capturas:
                numero_captura_actual = capturas_realizadas + 1
                
                # ══════════════════════════════════════
                # 1️⃣ CONFIGURACIÓN INICIAL DE CÁMARA
                # ══════════════════════════════════════
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    messagebox.showerror("Error", "No se pudo acceder a la cámara")
                    return

                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                captura_realizada = False
                frame_capturado = None

                # ═══════════════════════════════════════════════════════════════
                # 2️⃣ CREAR VENTANA DE VISTA PREVIA (OPENCV)
                # ═══════════════════════════════════════════════════════════════
                nombre_ventana = 'Captura de Rostro - Registro'
                
                cv2.namedWindow(nombre_ventana, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(nombre_ventana, 640, 540)
                
                # ───────────────────────────────────────────────────────────
                # ✅ CENTRAR VENTANA EN PANTALLA
                # ───────────────────────────────────────────────────────────
                screen_w = self.pantalla.winfo_screenwidth()
                screen_h = self.pantalla.winfo_screenheight()
                win_w = 640
                win_h = 540
                x = (screen_w // 2) - (win_w // 2)
                y = (screen_h // 2) - (win_h // 2)
                cv2.moveWindow(nombre_ventana, x, y)

                # ═══════════════════════════════════════════════════════════════
                # 3️⃣ BUCLE PRINCIPAL - VISTA PREVIA
                # ═══════════════════════════════════════════════════════════════
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame_preview = cv2.resize(frame, (640, 540))
                    
                    # ───────────────────────────────────────────────────────────
                    # 4️⃣ DIBUJAR ÓVALO GUÍA
                    # ───────────────────────────────────────────────────────────
                    center_x, center_y = 320, 270
                    axis_x, axis_y = 140, 180
                    
                    # Óvalo verde guía
                    cv2.ellipse(frame_preview, (center_x, center_y), (axis_x, axis_y), 0, 0, 360, (0, 255, 0), 3)
                    
                    # ───────────────────────────────────────────────────────────
                    # 5️⃣ INTERFAZ CON CONTADOR DE CAPTURAS
                    # ───────────────────────────────────────────────────────────
                    # Fondo superior
                    overlay = frame_preview.copy()
                    cv2.rectangle(overlay, (0, 0), (640, 70), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                    
                    # Título
                    cv2.putText(frame_preview, "REGISTRO DE ROSTRO", (200, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.putText(frame_preview, f"Usuario: {usuario}", (250, 55), cv2.FONT_HERSHEY_DUPLEX, 0.6, (200, 200, 200), 1)
                    
                    # 🔥 CONTADOR DE CAPTURAS (Alineado a la derecha)
                    texto_captura = f"Captura {numero_captura_actual}/{total_capturas}"
                    (text_w, text_h), _ = cv2.getTextSize(texto_captura, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.putText(frame_preview, texto_captura, (640 - text_w - 15, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
                    
                    # Fondo inferior
                    overlay = frame_preview.copy()
                    cv2.rectangle(overlay, (0, 500), (640, 540), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                    
                    # Instrucciones
                    cv2.putText(frame_preview, "ESPACIO: Capturar  |  ESC: Cancelar", (140, 530), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)

                    cv2.imshow(nombre_ventana, frame_preview)

                    # ───────────────────────────────────────────────────────────
                    # 6️⃣ CONTROL DE TECLAS
                    # ───────────────────────────────────────────────────────────
                    tecla = cv2.waitKey(1)
                    if tecla == 27:  # ESC - Cancelar TODO
                        cap.release()
                        cv2.destroyAllWindows()
                        messagebox.showinfo("Cancelado", "Registro cancelado")
                        pantalla_captura.destroy()
                        return
                    elif tecla == 32:  # ESPACIO - Capturar
                        frame_capturado = frame.copy()
                        captura_realizada = True
                        break

                cap.release()
                cv2.destroyAllWindows()

                if not captura_realizada:
                    continue

                # ═══════════════════════════════════════════════════════════════
                # 7️⃣ VALIDACIÓN DE LA CAPTURA
                # ═══════════════════════════════════════════════════════════════
                detector = MTCNN()
                pixeles_rgb = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2RGB)
                
                # Mejorar imagen con CLAHE
                lab = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                lab_mejorado = cv2.merge([l, a, b])
                frame_mejorado = cv2.cvtColor(lab_mejorado, cv2.COLOR_LAB2RGB)
                
                resultados = detector.detect_faces(frame_mejorado)

                # ───────────────────────────────────────────────────────────
                # 8️⃣ VALIDACIÓN: CANTIDAD DE ROSTROS
                # ───────────────────────────────────────────────────────────
                if len(resultados) == 0:
                    messagebox.showerror(
                        "Error - Sin Rostro",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        "No se detectó ningún rostro.\n"
                        "• Mejora la iluminación\n"
                        "• Centra tu rostro\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue  # Reintentar la misma captura

                if len(resultados) > 1:
                    messagebox.showerror(
                        "Error - Múltiples Rostros",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        "Se detectaron múltiples rostros.\n"
                        "Debe haber solo una persona.\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue

                # ───────────────────────────────────────────────────────────
                # 9️⃣ VALIDACIÓN: POSICIÓN DEL ROSTRO
                # ───────────────────────────────────────────────────────────
                x, y, ancho, alto = resultados[0]['box']
                x, y = abs(x), abs(y)
                confianza = resultados[0]['confidence']
                
                h_frame, w_frame = frame_capturado.shape[:2]
                centro_rostro_x = x + ancho // 2
                centro_rostro_y = y + alto // 2
                centro_frame_x = w_frame // 2
                centro_frame_y = h_frame // 2
                
                desplazamiento_x = abs(centro_rostro_x - centro_frame_x)
                desplazamiento_y = abs(centro_rostro_y - centro_frame_y)
                
                if desplazamiento_x > 150 or desplazamiento_y > 120:
                    messagebox.showerror(
                        "Error - Rostro Descentrado",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        "El rostro no está centrado.\n"
                        "Centra tu rostro en el óvalo verde\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue

                # ───────────────────────────────────────────────────────────
                # 🔟 VALIDACIÓN: TAMAÑO DEL ROSTRO
                # ───────────────────────────────────────────────────────────
                if ancho < 150 or alto < 150:
                    messagebox.showerror(
                        "Error - Rostro Pequeño",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        "El rostro es muy pequeño.\n"
                        "Acércate más a la cámara\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue
                
                if ancho > 500 or alto > 500:
                    messagebox.showerror(
                        "Error - Rostro Grande",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        "El rostro está muy cerca.\n"
                        "Aléjate un poco de la cámara\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue

                # ───────────────────────────────────────────────────────────
                # 1️⃣1️⃣ VALIDACIÓN: CALIDAD/ILUMINACIÓN
                # ───────────────────────────────────────────────────────────
                if confianza < 0.95:
                    messagebox.showerror(
                        "Error - Baja Calidad",
                        f"Captura {numero_captura_actual}/{total_capturas} falló\n\n"
                        f"Calidad: {confianza:.0%}\n"
                        "Mejora la iluminación\n\n"
                        "Presiona OK para reintentar"
                    )
                    continue

                # ───────────────────────────────────────────────────────────
                # 1️⃣2️⃣ RECORTAR Y PROCESAR ROSTRO
                # ───────────────────────────────────────────────────────────
                margen = int(min(ancho, alto) * 0.1)
                x_inicio = max(0, x - margen)
                y_inicio = max(0, y - margen)
                x_fin = min(frame_mejorado.shape[1], x + ancho + margen)
                y_fin = min(frame_mejorado.shape[0], y + alto + margen)
                
                rostro = frame_mejorado[y_inicio:y_fin, x_inicio:x_fin]
                rostro_resized = cv2.resize(rostro, (160, 160), interpolation=cv2.INTER_LANCZOS4)
                rostro_bgr = cv2.cvtColor(rostro_resized, cv2.COLOR_RGB2BGR)

                # ───────────────────────────────────────────────────────────
                # 1️⃣3️⃣ GUARDAR IMAGEN CON NÚMERO INCREMENTAL 🔥
                # ───────────────────────────────────────────────────────────
                if not os.path.exists("rostros_registro"):
                    os.makedirs("rostros_registro")
                
                # 🔥 FORMATO: usuario_1_rostro.jpg, usuario_2_rostro.jpg, usuario_3_rostro.jpg
                nombre_rostro_procesado = f"{usuario}_{numero_captura_actual}_rostro.jpg"
                ruta_guardado = f"rostros_registro/{nombre_rostro_procesado}"
                cv2.imwrite(ruta_guardado, rostro_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                # Agregar a la lista
                imagenes_guardadas.append(nombre_rostro_procesado)
                
                # ✅ CAPTURA EXITOSA
                capturas_realizadas += 1
                
                # Mostrar progreso
                if capturas_realizadas < total_capturas:
                    messagebox.showinfo(
                        "✓ Captura Exitosa",
                        f"Captura {capturas_realizadas}/{total_capturas} completada\n"
                        f"Calidad: {confianza:.0%}\n\n"
                        f"Prepárate para la siguiente captura"
                    )

            # ═══════════════════════════════════════════════════════════════
            # 1️⃣4️⃣ REGISTRAR EN BASE DE DATOS (DESPUÉS DE LAS 3 CAPTURAS)
            # ═══════════════════════════════════════════════════════════════
            conexion = self.conectar_db()
            if conexion:
                try:
                    cursor = conexion.cursor()
                    
                    # Guardar las 3 imágenes separadas por comas
                    imagenes_str = ",".join(imagenes_guardadas)
                    
                    query = """INSERT INTO usuarios (nombre_usuario, imagen_registro, fecha_registro) 
                            VALUES (%s, %s, NOW())"""
                    cursor.execute(query, (usuario, imagenes_str))
                    conexion.commit()
                    cursor.close()
                    conexion.close()

                    pantalla_captura.destroy()

                    messagebox.showinfo(
                        "✓ Registro Exitoso Completo",
                        f"Usuario: {usuario}\n"
                        f"Capturas realizadas: {total_capturas}\n"
                        f"Imágenes guardadas:\n"
                        f"  • {imagenes_guardadas[0]}\n"
                        f"  • {imagenes_guardadas[1]}\n"
                        f"  • {imagenes_guardadas[2]}\n\n"
                        f"✓ Ya puedes marcar asistencia"
                    )
                    
                except mysql.connector.Error as err:
                    # Si falla el registro, eliminar las imágenes
                    for img in imagenes_guardadas:
                        ruta = f"rostros_registro/{img}"
                        if os.path.exists(ruta):
                            os.remove(ruta)
                    messagebox.showerror("Error BD", f"Error al guardar:\n{err}")
                    if conexion.is_connected():
                        conexion.close()
            else:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")

        except Exception as e:
            messagebox.showerror("Error", f"Error en el registro:\n{str(e)}")
   
    def ventana_marcar_asistencia(self):
        """Crea la ventana de preparación para marcar asistencia."""
        
        # Configuración de la ventana
        self.pantalla_asistencia = Toplevel(self.pantalla)
        self.pantalla_asistencia.title("Marcar Asistencia")
        self.centrar_ventana(self.pantalla_asistencia, 400, 450)

        # =========================
        # HEADER
        # =========================
        Label(
            self.pantalla_asistencia,
            text="MARCAR ASISTENCIA",
            bg="#3500C5",
            fg="white",
            width=400,
            height=2,
            font=("Arial", 12, "bold")
        ).pack()

        # Espaciador
        Label(self.pantalla_asistencia, text="").pack(pady=5)

        # =========================
        # FRAME DE INSTRUCCIONES
        # =========================
        frame_instrucciones = Frame(
            self.pantalla_asistencia,
            bg="#FFF3E0",
            relief=RIDGE,
            borderwidth=3
        )
        frame_instrucciones.pack(pady=10, padx=20, fill=BOTH)

        # Título de instrucciones
        Label(
            frame_instrucciones,
            text="PREPARACIÓN PARA MARCAR ASISTENCIA",
            font=("Arial", 11, "bold"),
            bg="#FFE8C4",
            fg="#F0A400"
        ).pack(pady=8)

        # Lista de instrucciones
        instrucciones = [
            "✓ Centra tu rostro en la CÁMARA",
            "✓ Asegúrate de tener buena iluminación",
            "✓ Asegúrate de estar registrado previamente"
        ]

        for texto in instrucciones:
            Label(
                frame_instrucciones,
                text=texto,
                font=("Arial", 10),
                bg="#FFF3E0",
                anchor="w"
            ).pack(padx=20, pady=3, fill=X)

        # Espaciador
        Label(self.pantalla_asistencia, text="").pack(pady=2)

        # =========================
        # CAMPO DE OBSERVACIÓN
        # =========================
        Label(
            self.pantalla_asistencia,
            text="Observación (solo si llega tarde):",
            font=("Arial", 10, "bold"),
            bg="#B4F8BA",
            anchor="center"
        ).pack(padx=20, pady=(5, 2), fill=X)

        self.usuario_observacion = StringVar()
        entry_usuario_obs = Entry(
            self.pantalla_asistencia,
            textvariable=self.usuario_observacion,
            font=("Arial", 13),
            width=30,
            justify="left"
        )
        entry_usuario_obs.pack(pady=6)
        entry_usuario_obs.focus()

        # Espaciador
        Label(self.pantalla_asistencia, text="").pack(pady=2)

        # =========================
        # BOTONES
        # =========================
        
        # Botón Iniciar Captura
        Button(
            self.pantalla_asistencia,
            text="📷 INICIAR CAPTURA",
            width=30,
            height=2,
            bg="#27B42B",
            fg="white",
            font=("Arial", 10, "bold"),
            command=lambda: self.capturar_asistencia(self.pantalla_asistencia)
        ).pack(pady=5)

        # Botón Cancelar
        Button(
            self.pantalla_asistencia,
            text="❌ Cancelar",
            width=30,
            height=2,
            bg="#f02a1c",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.pantalla_asistencia.destroy
        ).pack(pady=5)

    def capturar_asistencia(self, pantalla_asistencia):
        try:
            # ═══════════════════════════════════════════════════════════════
            # 1️⃣ CONFIGURACIÓN INICIAL DE CÁMARA
            # ═══════════════════════════════════════════════════════════════
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "No se pudo acceder a la cámara")
                return

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            captura_realizada = False
            frame_capturado = None

            # ═══════════════════════════════════════════════════════════════
            # 2️⃣ CREAR VENTANA DE VISTA PREVIA (OPENCV)
            # ═══════════════════════════════════════════════════════════════
            nombre_ventana = 'Marcar Asistencia'
                
            cv2.namedWindow(nombre_ventana, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(nombre_ventana, 640, 540)
                
            # ───────────────────────────────────────────────────────────
            # ✅ CENTRAR VENTANA EN PANTALLA
            # ───────────────────────────────────────────────────────────
            screen_w = self.pantalla.winfo_screenwidth()
            screen_h = self.pantalla.winfo_screenheight()
            win_w = 640
            win_h = 540
            x = (screen_w // 2) - (win_w // 2)
            y = (screen_h // 2) - (win_h // 2)
            cv2.moveWindow(nombre_ventana, x, y)

            # ═══════════════════════════════════════════════════════════════
            # 3️⃣ BUCLE PRINCIPAL - VISTA PREVIA
            # ═══════════════════════════════════════════════════════════════
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_preview = cv2.resize(frame, (640, 540))
                
                # ───────────────────────────────────────────────────────────
                # 4️⃣ DIBUJAR ÓVALO GUÍA (IGUAL QUE REGISTRO)
                # ───────────────────────────────────────────────────────────
                center_x, center_y = 320, 270
                axis_x, axis_y = 140, 180
                
                # Óvalo verde guía
                cv2.ellipse(frame_preview, (center_x, center_y), (axis_x, axis_y),  0, 0, 360, (0, 255, 0), 3)
                
                # ───────────────────────────────────────────────────────────
                # 5️⃣ INTERFAZ SIMPLE
                # ───────────────────────────────────────────────────────────
                # Fondo superior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 0), (640, 70), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                
                # Título
                cv2.putText(frame_preview, "MARCAR ASISTENCIA", (210, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
                    
                cv2.putText(frame_preview, f"Centra tu rostro en el Ovalo Verde", (160, 55), cv2.FONT_HERSHEY_DUPLEX, 0.6, (200, 200, 200), 1)
                    
                
                # Fondo inferior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 500), (640, 540), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                # Instrucciones
                cv2.putText(frame_preview, "ESPACIO: Capturar  |  ESC: Cancelar", (140, 530), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)

                cv2.imshow(nombre_ventana, frame_preview)

                # ───────────────────────────────────────────────────────────
                # 6️⃣ CONTROL DE TECLAS
                # ───────────────────────────────────────────────────────────
                tecla = cv2.waitKey(1)
                if tecla == 27:  # ESC
                    cap.release()
                    cv2.destroyAllWindows()
                    pantalla_asistencia.destroy()
                    return
                elif tecla == 32:  # ESPACIO - Capturar
                    frame_capturado = frame.copy()
                    captura_realizada = True
                    break

            cap.release()
            cv2.destroyAllWindows()

            if not captura_realizada:
                messagebox.showinfo("Cancelado", "Captura cancelada")
                return

            # ═══════════════════════════════════════════════════════════════
            # 7️⃣ VALIDACIÓN DE LA CAPTURA (IGUAL QUE REGISTRO)
            # ═══════════════════════════════════════════════════════════════
            detector = MTCNN()
            pixeles_rgb = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2RGB)
            
            # Mejorar imagen con CLAHE
            lab = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab_mejorado = cv2.merge([l, a, b])
            frame_mejorado = cv2.cvtColor(lab_mejorado, cv2.COLOR_LAB2RGB)
            
            resultados = detector.detect_faces(frame_mejorado)

            # ───────────────────────────────────────────────────────────
            # 8️⃣ VALIDACIÓN: CANTIDAD DE ROSTROS
            # ───────────────────────────────────────────────────────────
            if len(resultados) == 0:
                messagebox.showerror(
                    "Error - Sin Rostro",
                    "No se detectó ningún rostro.\n\n"
                    "• Mejora la iluminación\n"
                    "• Centra tu rostro"
                )
                return

            if len(resultados) > 1:
                messagebox.showerror(
                    "Error - Múltiples Rostros", 
                    "Se detectaron múltiples rostros.\n\n"
                    "Debe haber solo una persona en el encuadre."
                )
                return

            # ───────────────────────────────────────────────────────────
            # 9️⃣ VALIDACIÓN: POSICIÓN DEL ROSTRO
            # ───────────────────────────────────────────────────────────
            x, y, ancho, alto = resultados[0]['box']
            x, y = abs(x), abs(y)
            confianza = resultados[0]['confidence']
            
            # Calcular centro del rostro
            h_frame, w_frame = frame_capturado.shape[:2]
            centro_rostro_x = x + ancho // 2
            centro_rostro_y = y + alto // 2
            centro_frame_x = w_frame // 2
            centro_frame_y = h_frame // 2
            
            # Verificar centrado
            desplazamiento_x = abs(centro_rostro_x - centro_frame_x)
            desplazamiento_y = abs(centro_rostro_y - centro_frame_y)
            
            if desplazamiento_x > 150 or desplazamiento_y > 120:
                messagebox.showerror(
                    "Error - Rostro Descentrado",
                    "El rostro no está centrado.\n\n"
                    "Centra tu rostro en el óvalo verde\n"
                    "y vuelve a intentar."
                )
                return

            # ───────────────────────────────────────────────────────────
            # 🔟 VALIDACIÓN: TAMAÑO DEL ROSTRO
            # ───────────────────────────────────────────────────────────
            if ancho < 150 or alto < 150:
                messagebox.showerror(
                    "Error - Rostro Pequeño",
                    "El rostro es muy pequeño.\n\n"
                    "Acércate más a la cámara\n"
                    "y vuelve a intentar."
                )
                return
            
            if ancho > 500 or alto > 500:
                messagebox.showerror(
                    "Error - Rostro Grande",
                    "El rostro está muy cerca.\n\n"
                    "Aléjate un poco de la cámara\n"
                    "y vuelve a intentar."
                )
                return

            # ───────────────────────────────────────────────────────────
            # 1️⃣1️⃣ VALIDACIÓN: CALIDAD/ILUMINACIÓN
            # ───────────────────────────────────────────────────────────
            if confianza < 0.95:
                messagebox.showerror(
                    "Error - Baja Calidad",
                    f"Calidad de detección: {confianza:.0%}\n\n"
                    "Mejora la iluminación\n"
                    "y vuelve a intentar."
                )
                return

            # ───────────────────────────────────────────────────────────
            # 1️⃣2️⃣ RECORTAR Y PROCESAR ROSTRO
            # ───────────────────────────────────────────────────────────
            # Añadir margen al recorte (10%)
            margen = int(min(ancho, alto) * 0.1)
            x_inicio = max(0, x - margen)
            y_inicio = max(0, y - margen)
            x_fin = min(frame_mejorado.shape[1], x + ancho + margen)
            y_fin = min(frame_mejorado.shape[0], y + alto + margen)
            
            rostro = frame_mejorado[y_inicio:y_fin, x_inicio:x_fin]

            # Redimensionar a 160x160
            rostro_resized = cv2.resize(rostro, (160, 160), interpolation=cv2.INTER_LANCZOS4)
            rostro_bgr = cv2.cvtColor(rostro_resized, cv2.COLOR_RGB2BGR)

            # ───────────────────────────────────────────────────────────
            # 1️⃣3️⃣ GUARDAR IMAGEN TEMPORAL
            # ───────────────────────────────────────────────────────────
            if not os.path.exists("rostros_asistencia"):
                os.makedirs("rostros_asistencia")
                
            fecha_hora_actual = datetime.now()

            # PARA ARCHIVOS (sin :)
            fecha_hora_str = fecha_hora_actual.strftime("%Y-%m-%d_%H-%M-%S")

            temp_login = f"rostros_asistencia/temp_asistencia_{fecha_hora_str}.jpg"
            cv2.imwrite(temp_login, rostro_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # ═══════════════════════════════════════════════════════════════
            # 1️⃣4️⃣ COMPARAR CON ROSTROS REGISTRADOS (MEJORADO - 3 IMÁGENES)
            # ═══════════════════════════════════════════════════════════════
            usuario_encontrado = None
            mejor_distancia = float('inf')
            umbral_distancia = 0.40  # Umbral de Facenet512      
            
            
            ##mejoras q se puede hacer en el humbral
            # Si tienes muchos FALSOS NEGATIVOS (no reconoce usuarios válidos):
            #umbral_distancia = 0.45  # En capturar_asistencia (más permisivo)

            # Si tienes muchos FALSOS POSITIVOS (reconoce usuarios incorrectos):
            #umbral_distancia = 0.35  # En capturar_asistencia (más estricto)
            
            
            
            imagen_match = None  # Para saber cuál imagen hizo match

            # 🔥 Recorrer todas las imágenes en rostros_registro
            for archivo in os.listdir("rostros_registro"):
                if archivo.endswith("_rostro.jpg"):
                    # Comparar con esta imagen
                    distancia = self.comparar_rostros(
                        f"rostros_registro/{archivo}", 
                        temp_login
                    )
                    
                    # Buscar la MENOR distancia (más similar)
                    if distancia < mejor_distancia and distancia < umbral_distancia:
                        mejor_distancia = distancia
                        imagen_match = archivo
                        
                        # 🔥 EXTRAER NOMBRE DE USUARIO (quitar número y "_rostro.jpg")
                        # Ejemplos:
                        # "juan_1_rostro.jpg" → "juan"
                        # "maria_2_rostro.jpg" → "maria"
                        # "pedro_3_rostro.jpg" → "pedro"
                        partes = archivo.replace("_rostro.jpg", "").split("_")
                        # Si tiene formato: usuario_numero_rostro.jpg
                        if len(partes) >= 2 and partes[-1].isdigit():
                            usuario_encontrado = "_".join(partes[:-1])  # Todo menos el número
                        else:
                            # Fallback por si tiene formato antiguo
                            usuario_encontrado = archivo.replace("_rostro.jpg", "")

            # ───────────────────────────────────────────────────────────
            # 1️⃣5️⃣ VERIFICAR SI SE ENCONTRÓ COINCIDENCIA
            # ───────────────────────────────────────────────────────────
            if usuario_encontrado and mejor_distancia < umbral_distancia:
                # Convertir distancia a porcentaje de similitud para mostrar
                similitud_porcentual = max(0, (1 - (mejor_distancia / umbral_distancia)))
                
                # ───────── FECHA Y HORA ─────────
                fecha_actual = fecha_hora_actual.strftime("%Y-%m-%d")
                hora_actual  = fecha_hora_actual.strftime("%H:%M:%S")
                fecha_hora_formato_db = fecha_hora_actual.strftime("%Y-%m-%d %H:%M:%S")
                nombre_imagen_asistencia = f"{usuario_encontrado}_{fecha_hora_str}.jpg"
                ruta_imagen_final = f"rostros_asistencia/{nombre_imagen_asistencia}"
                os.rename(temp_login, ruta_imagen_final)
                
                # ═══════════════════════════════════════════════════════════════
                # 1️⃣6️⃣ GUARDAR EN BASE DE DATOS
                # ═══════════════════════════════════════════════════════════════
                # ───────── REGLAS DE ASISTENCIA ─────────
                tipo, estado, minutos_extra = self.determinar_tipo_estado_y_minutos(fecha_hora_actual)
                # Interpretación:
                if tipo == 1:
                    tipo_str = "ENTRADA"
                elif tipo == 2:
                    tipo_str = "SALIDA"
                else:
                    tipo_str = "FUERA DE HORARIO"

                if estado == 1:
                    estado_str = "NORMAL"
                elif estado == 2:
                    estado_str = "TARDANZA"
                else:
                    estado_str = "INDETERMINADO"
                    
                # ───────── OBSERVACION ─────────   
                if estado == 2:  # TARDANZA
                    # Usuario debe justificar tardanza
                    justificacion = self.usuario_observacion.get().strip()
                    if justificacion:
                        observacion = f"{estado_str}--{justificacion}"
                    else:
                        observacion = f"{estado_str}--Sin justificación"
                        
                elif minutos_extra > 0:  # TIEMPO EXTRA (entrada temprana o salida tardía)
                    if tipo == 1:  # Entrada temprana
                        observacion = f"{tipo_str} TEMPRANA (+{minutos_extra} min extra)"
                    else:  # Salida tardía
                        observacion = f"{tipo_str} TARDÍA (+{minutos_extra} min extra)"
                else:  # NORMAL
                    observacion = tipo_str
                    
                conexion = self.conectar_db()
                if conexion:
                    try:
                        cursor = conexion.cursor()
                        query = """
                                INSERT INTO asistencias
                                (nombre_usuario, fecha, hora, tipo, estado, minutos_extra, observacion, similitud, imagen_asistencia)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                        cursor.execute(query, (
                            usuario_encontrado,
                            fecha_actual,
                            hora_actual,
                            tipo,
                            estado,
                            minutos_extra,
                            observacion,
                            f"{mejor_distancia:.4f}",
                            nombre_imagen_asistencia
                        ))
                        conexion.commit()
                        cursor.close()
                        conexion.close()

                        pantalla_asistencia.destroy()

                        messagebox.showinfo(
                            "✓ Asistencia Registrada",
                            f"¡Bienvenido(a) {usuario_encontrado}!\n\n"
                            f"Fecha: {fecha_hora_formato_db}\n"
                            f"Confianza: {similitud_porcentual:.1%}\n"
                            f"Distancia: {mejor_distancia:.3f}\n"
                            f"Calidad captura: {confianza:.0%}\n"
                            f"Match con: {imagen_match}\n"
                            f"Imagen guardada: {nombre_imagen_asistencia}"
                        )
                        
                    except mysql.connector.Error as err:
                        messagebox.showerror("Error BD", f"Error al guardar:\n{err}")
                        if conexion.is_connected():
                            conexion.close()
            else:
                # Eliminar imagen temporal si no se reconoció
                if os.path.exists(temp_login):
                    os.remove(temp_login)
                
                messagebox.showerror(
                    "✗ Acceso Denegado",
                    f"Rostro no reconocido\n\n"
                    f"Menor distancia encontrada: {mejor_distancia:.3f}\n"
                    f"Umbral requerido: {umbral_distancia:.2f}\n"
                    f"({'%.1f' % (mejor_distancia/umbral_distancia*100)}% del umbral)\n\n"
                    f"Si no estás registrado, regístrate primero"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Error al marcar asistencia:\n{str(e)}")
    
    def determinar_tipo_estado_y_minutos(self, fecha_hora_actual):
        """
        Determina tipo de asistencia, estado y minutos extra.
        
        Returns:
            tuple: (tipo, estado, minutos_extra)
            - tipo: 1=ENTRADA, 2=SALIDA
            - estado: 1=NORMAL, 2=TARDANZA
            - minutos_extra: int (positivo=extras trabajadas, negativo=llegada temprana)
        """
        hora = fecha_hora_actual.time()
        minutos_actuales = fecha_hora_actual.hour * 60 + fecha_hora_actual.minute

        # Entrada Mañana
        ENTRADA_MANANA_INICIO = 8 * 60       # 08:00 = 480 min
        ENTRADA_MANANA_FIN = 8 * 60 + 20     # 08:20 = 510 min
        
        # Entrada Tarde
        ENTRADA_TARDE_INICIO = 14 * 60       # 14:00 = 840 min
        ENTRADA_TARDE_FIN = 15 * 60 + 20     # 15:20 = 920 min
        
        # Salida Mediodía
        SALIDA_MEDIODIA_INICIO = 12 * 60 + 55  # 12:55 = 775 min
        SALIDA_MEDIODIA_FIN = 14 * 60          # 14:00 = 840 min
        
        # Salida Noche
        SALIDA_NOCHE_INICIO = 17 * 60 + 55   # 17:55 = 1075 min
        SALIDA_NOCHE_FIN = 18 * 60 + 15      # 18:15 = 1095 min

        # ═══════════════════════════════════════════════════════════════
        # 🌅 BLOQUE 1: ENTRADA MAÑANA
        # ═══════════════════════════════════════════════════════════════
        # Caso 1: ANTES de 08:00 (Entrada temprana con tiempo extra)
        if minutos_actuales < ENTRADA_MANANA_INICIO:
            minutos_extra = ENTRADA_MANANA_INICIO - minutos_actuales  # Positivo
            return 1, 1, minutos_extra
        
        # Caso 2: 08:00 - 08:20 (Entrada normal)
        if ENTRADA_MANANA_INICIO <= minutos_actuales <= ENTRADA_MANANA_FIN:
            return 1, 1, 0
        
        # Caso 3: 08:20 - 12:55 (Entrada tarde sin extra)
        if ENTRADA_MANANA_FIN < minutos_actuales < SALIDA_MEDIODIA_INICIO:
            return 1, 2, 0

        # ═══════════════════════════════════════════════════════════════
        # 🌆 BLOQUE 2: SALIDA MEDIODÍA
        # ═══════════════════════════════════════════════════════════════
        if SALIDA_MEDIODIA_INICIO <= minutos_actuales <= SALIDA_MEDIODIA_FIN:
            return 2, 1, 0

        # ═══════════════════════════════════════════════════════════════
        # 🌤️ BLOQUE 3: ENTRADA TARDE
        # ═══════════════════════════════════════════════════════════════
        
        # ✅ Caso: 14:00 - 15:20 (Entrada normal)
        if ENTRADA_TARDE_INICIO <= minutos_actuales <= ENTRADA_TARDE_FIN:
            return 1, 1, 0
        
        # ✅ Caso: 15:20 - 17:55 (Entrada tarde)
        if ENTRADA_TARDE_FIN < minutos_actuales < SALIDA_NOCHE_INICIO:
            return 1, 2, 0

        # ═══════════════════════════════════════════════════════════════
        # 🌙 BLOQUE 4: SALIDA NOCHE
        # ═══════════════════════════════════════════════════════════════
        
        #  Caso: 17:55 - 18:15 (Salida normal)
        if SALIDA_NOCHE_INICIO <= minutos_actuales <= SALIDA_NOCHE_FIN:
            return 2, 1, 0
        
        # Caso: DESPUÉS de 18:15 (Salida tardía con tiempo extra)
        if minutos_actuales > SALIDA_NOCHE_FIN:
            minutos_extra = minutos_actuales - SALIDA_NOCHE_FIN
            return 2, 1, minutos_extra

        # ═══════════════════════════════════════════════════════════════
        # ⚠️ BLOQUE 5: FUERA DE HORARIO 
        # ═══════════════════════════════════════════════════════════════
        # Esto cubre horarios extraños como 02:00 AM, 23:00 PM, etc.
        return 0, 0, 0  # 0 = INDETERMINADO

    def comparar_rostros(self, img1_path, img2_path):
        """
        Compara dos rostros y retorna la DISTANCIA (menor = más similar)
        Retorna: float (0.0 = idénticos, 0.4+ = diferentes, inf = error)
        """
        try:
            # ───────────────────────────────────────────────────────────
            # 1️⃣ VALIDAR EXISTENCIA DE ARCHIVOS
            # ───────────────────────────────────────────────────────────
            if not os.path.exists(img1_path) or not os.path.exists(img2_path):
                print(f"⚠️ Archivo no existe: {img1_path} o {img2_path}")
                return float('inf')
            
            # ───────────────────────────────────────────────────────────
            # 2️⃣ USAR DEEPFACE (MÉTODO PRINCIPAL)
            # ───────────────────────────────────────────────────────────
            resultado = DeepFace.verify(
                img1_path=img1_path,
                img2_path=img2_path,
                model_name='Facenet512',      # Modelo más preciso
                detector_backend='skip',       # Ya detectamos con MTCNN
                distance_metric='cosine',      # Mejor para embeddings
                enforce_detection=False,       # No fallar si no detecta
                align=True                     # ✅ Alinear rostros para mejor precisión
            )
            
            distancia = resultado['distance']
            
            # ───────────────────────────────────────────────────────────
            # 3️⃣ LOGGING PARA DEBUG (OPCIONAL)
            # ───────────────────────────────────────────────────────────
            # print(f"📊 Distancia: {distancia:.4f} | {img1_path.split('/')[-1]} vs {img2_path.split('/')[-1]}")
            
            return distancia
            
        except Exception as e:
            print(f"❌ Error DeepFace: {e}")
            print(f"   Archivos: {img1_path} | {img2_path}")
            
            # ───────────────────────────────────────────────────────────
            # 4️⃣ FALLBACK A ORB (MÉTODO DE RESPALDO)
            # ───────────────────────────────────────────────────────────
            similitud_orb = self.comparar_rostros_orb(img1_path, img2_path)
            
            # ✅ Convertir similitud ORB (0-1) a distancia compatible
            # Similitud 1.0 → distancia 0.0 (muy similar)
            # Similitud 0.0 → distancia 1.0 (muy diferente)
            distancia_orb = 1.0 - similitud_orb
            
            print(f"🔄 Fallback ORB activado | Similitud: {similitud_orb:.2f} → Distancia: {distancia_orb:.2f}")
            
            return distancia_orb

    def comparar_rostros_orb(self, img1_path, img2_path):
        """
        Fallback con ORB cuando DeepFace falla
        Retorna: similitud (0.0 = diferentes, 1.0 = idénticos)
        """
        try:
            # ───────────────────────────────────────────────────────────
            # 1️⃣ CARGAR IMÁGENES EN ESCALA DE GRISES
            # ───────────────────────────────────────────────────────────
            img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                print(f"⚠️ ORB: No se pudieron cargar las imágenes")
                return 0.0
            
            # ───────────────────────────────────────────────────────────
            # 2️⃣ ECUALIZAR HISTOGRAMA (MEJORA EN ILUMINACIÓN DIFERENTE)
            # ───────────────────────────────────────────────────────────
            img1 = cv2.equalizeHist(img1)
            img2 = cv2.equalizeHist(img2)
            
            # ───────────────────────────────────────────────────────────
            # 3️⃣ DETECTAR CARACTERÍSTICAS ORB
            # ───────────────────────────────────────────────────────────
            orb = cv2.ORB_create(
                nfeatures=2000,      # Más features = mejor precisión
                scaleFactor=1.2,     # Factor de escala de pirámide
                nlevels=8,           # Niveles de pirámide
                edgeThreshold=15,    # Tamaño del borde
                firstLevel=0,
                WTA_K=2,
                scoreType=cv2.ORB_HARRIS_SCORE,
                patchSize=31,
                fastThreshold=20
            )
            
            kp1, desc1 = orb.detectAndCompute(img1, None)
            kp2, desc2 = orb.detectAndCompute(img2, None)
            
            if desc1 is None or desc2 is None:
                print(f"⚠️ ORB: No se detectaron descriptores")
                return 0.0
            
            # ───────────────────────────────────────────────────────────
            # 4️⃣ EMPAREJAR CARACTERÍSTICAS
            # ───────────────────────────────────────────────────────────
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(desc1, desc2)
            
            if len(matches) == 0:
                return 0.0
            
            # ───────────────────────────────────────────────────────────
            # 5️⃣ FILTRAR MEJORES MATCHES
            # ───────────────────────────────────────────────────────────
            # Ordenar por distancia (menor = mejor)
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Tomar los mejores 100 matches o todos si hay menos
            top_matches = matches[:min(100, len(matches))]
            
            # Contar matches de alta calidad (distancia < 50)
            buenos_matches = [m for m in top_matches if m.distance < 50]
            
            
            ##MEJORA DE PRECISION
            #buenos_matches = [m for m in top_matches if m.distance < 60]  # Más permisivo
            #buenos_matches = [m for m in top_matches if m.distance < 40]  # Más estricto
            
            
            # ───────────────────────────────────────────────────────────
            # 6️⃣ CALCULAR SIMILITUD
            # ───────────────────────────────────────────────────────────
            if len(top_matches) == 0:
                return 0.0
            
            # Similitud basada en porcentaje de buenos matches
            similitud = len(buenos_matches) / len(top_matches)
            
            # ✅ Ajuste adicional basado en distancia promedio
            distancia_promedio = sum(m.distance for m in buenos_matches) / max(1, len(buenos_matches))
            factor_calidad = max(0, 1 - (distancia_promedio / 50))  # Normalizar distancia
            
            similitud_ajustada = similitud * factor_calidad
            
            return similitud_ajustada
            
        except Exception as e:
            print(f"❌ Error ORB: {e}")
            return 0.0
    def iniciar(self):
        self.pantalla.mainloop()

# Ejecutar el sistema
if __name__ == "__main__":
    sistema = SistemaAsistencia()
    sistema.iniciar()
    
    
    
    
#pip install pyinstaller
#pyinstaller --onefile --icon=icono.ico GEmanuel.py

#pyinstaller --onefile --windowed --name="Sistema_Asistencia" --icon="icono.ico" Login_Vision.py
