from tkinter import *
from tkinter import messagebox
import os
import cv2
from matplotlib import pyplot as plt
from mtcnn.mtcnn import MTCNN
import numpy as np
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
from deepface import DeepFace
# Cargar variables de entorno
load_dotenv()

class SistemaAsistencia:
    def __init__(self):
        self.pantalla = Tk()
        self.pantalla.title("Sistema de Control de Asistencia")
        
        # 🔹 Tamaño de la ventana
        ancho = 400
        alto = 400
        
        # 🔹 Tamaño de la pantalla
        pantalla_ancho = self.pantalla.winfo_screenwidth()
        pantalla_alto = self.pantalla.winfo_screenheight()
        
        # 🔹 Posición centrada
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        self.pantalla.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.pantalla.resizable(False, False)
        
        # Crear carpetas si no existen
        if not os.path.exists("rostros_registro"):
            os.makedirs("rostros_registro")
        if not os.path.exists("rostros_asistencia"):
            os.makedirs("rostros_asistencia")
        
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
    
    def crear_pantalla_principal(self):
        # Título
        Label(self.pantalla, text="CONTROL DE ASISTENCIA", 
              bg="gray", fg="white", width="300", height="2", 
              font=("Verdana", 13)).pack()
        
        Label(self.pantalla, text="").pack(pady=10)
        
        # Botón Registro
        Button(self.pantalla, text="👤 Registro de Usuario", height="2", width="35",
               bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
               command=self.ventana_registro).pack(pady=10)
        
        
        # Botón Marcar Asistencia (principal)
        Button(self.pantalla, text="📋 MARCAR ASISTENCIA", height="2", width="35",
               bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
               command=self.ventana_marcar_asistencia).pack(pady=10)
        
        # Botón Salir
        Button(self.pantalla, text="❌ Salir", height="2", width="35",
               bg="#f44336", fg="white", font=("Arial", 11, "bold"),
               command=self.pantalla.quit).pack(pady=10)
    
    def ventana_registro(self):
        self.pantalla_registro = Toplevel(self.pantalla)
        self.pantalla_registro.title("Registro de Usuario")
        # 🔹 Tamaño de la ventana
        ancho = 350
        alto = 350
        # 🔹 Tamaño de la pantalla
        pantalla_ancho = self.pantalla_registro.winfo_screenwidth()
        pantalla_alto = self.pantalla_registro.winfo_screenheight()
        
        # 🔹 Posición centrada
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        self.pantalla_registro.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.pantalla_registro.resizable(False, False)

        Label(
            self.pantalla_registro,
            text="REGISTRO DE NUEVO USUARIO",
            bg="#2196F3",
            fg="white",
            width="300",
            height="2",
            font=("Arial", 12, "bold")
        ).pack()

        Label(self.pantalla_registro, text="").pack(pady=10)

        Label(
            self.pantalla_registro,
            text="Ingrese nombre de usuario:",
            font=("Arial", 11, "bold")
        ).pack()

        self.usuario_registro = StringVar()    # Variable para almacenar el nombre de usuario
        entry_usuario = Entry(
            self.pantalla_registro,
            textvariable=self.usuario_registro,
            font=("Arial", 14),
            width=25,
            justify="center"
        )
        entry_usuario.pack(pady=10)
        entry_usuario.focus()

        Label(self.pantalla_registro, text="").pack(pady=5)

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
        self.pantalla_captura = Toplevel(self.pantalla)
        self.pantalla_captura.title("Captura de Rostro - Registro")
        # 🔹 Tamaño de la ventana
        ancho = 500
        alto = 500
        # 🔹 Tamaño de la pantalla
        pantalla_ancho = self.pantalla_captura.winfo_screenwidth()
        pantalla_alto = self.pantalla_captura.winfo_screenheight()
        # 🔹 Posición centrada
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        self.pantalla_captura.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.pantalla_captura.resizable(False, False)


        Label(
            self.pantalla_captura,
            text="PREPARACIÓN PARA CAPTURA",
            bg="#FF9800",
            fg="white",
            width="300",
            height="2",
            font=("Arial", 12, "bold")
        ).pack()

        Label(self.pantalla_captura, text="").pack(pady=10)

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
            bg="#FFF3E0",
            fg="#E65100"
        ).pack(pady=10)

        Label(frame_instrucciones, text="✓ Centra tu rostro, se realizara 3 capturas",
            font=("Arial", 10), bg="#FFF3E0", anchor="w").pack(padx=20, pady=3)

        Label(frame_instrucciones, text="✓ Asegúrate de tener buena iluminación",
            font=("Arial", 10), bg="#FFF3E0", anchor="w").pack(padx=20, pady=3)

        Label(frame_instrucciones, text="✓ Retira lentes o accesorios si es posible",
            font=("Arial", 10), bg="#FFF3E0", anchor="w").pack(padx=20, pady=3)

        Label(frame_instrucciones, text="✓ Mantén una expresión neutral",
            font=("Arial", 10), bg="#FFF3E0", anchor="w").pack(padx=20, pady=3)

        Label(self.pantalla_captura, text="").pack(pady=10)

        Button(
            self.pantalla_captura,
            text="📷 INICIAR CAPTURA",
            width=30,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            command=lambda: self.capturar_rostro_registro(usuario)
        ).pack(pady=10)

        Button(
            self.pantalla_captura,
            text="Cancelar",
            width=30,
            height=2,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            command=self.pantalla_captura.destroy
        ).pack(pady=10)

    def capturar_rostro_registro(self, usuario):
        """
        Captura y registra el rostro de un usuario.
        Validación solo al momento de capturar (máximo rendimiento).
        """
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
            # 2️⃣ CREAR VENTANA DE VISTA PREVIA
            # ═══════════════════════════════════════════════════════════════
            cv2.namedWindow('Captura de Rostro - Registro', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Captura de Rostro - Registro', 640, 540)   #640*480

            # ═══════════════════════════════════════════════════════════════
            # 3️⃣ BUCLE PRINCIPAL - SOLO VISTA PREVIA
            # ═══════════════════════════════════════════════════════════════
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_preview = cv2.resize(frame, (640, 540)) #640*480
                
                # ───────────────────────────────────────────────────────────
                # 4️⃣ DIBUJAR ÓVALO GUÍA (ESTÁTICO)
                # ───────────────────────────────────────────────────────────
                center_x, center_y = 320, 270  #320*240
                axis_x, axis_y = 140, 180
                
                # Óvalo verde guía
                cv2.ellipse(frame_preview, (center_x, center_y), (axis_x, axis_y), 
                        0, 0, 360, (0, 255, 0), 3)
                
                # ───────────────────────────────────────────────────────────
                # 5️⃣ INTERFAZ SIMPLE
                # ───────────────────────────────────────────────────────────
                # Fondo superior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 0), (640, 70), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                # Título
                cv2.putText(frame_preview, "REGISTRO DE ROSTRO", 
                        (160, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame_preview, f"Usuario: {usuario}", 
                        (220, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                
                # Fondo inferior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 500), (640, 540), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                # Instrucciones
                cv2.putText(frame_preview, "ESPACIO: Capturar  |  ESC: Cancelar", 
                        (140, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                cv2.imshow('Captura de Rostro - Registro', frame_preview)

                # ───────────────────────────────────────────────────────────
                # 6️⃣ CONTROL DE TECLAS
                # ───────────────────────────────────────────────────────────
                tecla = cv2.waitKey(1)
                if tecla == 27:  # ESC
                    break
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
            # 7️⃣ AQUÍ EMPIEZA LA VALIDACIÓN (SOLO UNA VEZ)
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
            # 1️⃣3️⃣ GUARDAR IMAGEN
            # ───────────────────────────────────────────────────────────
            if not os.path.exists("rostros_registro"):
                os.makedirs("rostros_registro")
            
            nombre_rostro_procesado = f"{usuario}_rostro.jpg"
            ruta_guardado = f"rostros_registro/{nombre_rostro_procesado}"
            cv2.imwrite(ruta_guardado, rostro_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # ═══════════════════════════════════════════════════════════════
            # 1️⃣4️⃣ REGISTRAR EN BASE DE DATOS
            # ═══════════════════════════════════════════════════════════════
            conexion = self.conectar_db()
            if conexion:
                try:
                    cursor = conexion.cursor()
                    query = """INSERT INTO usuarios (nombre_usuario, imagen_registro, fecha_registro) 
                            VALUES (%s, %s, NOW())"""
                    cursor.execute(query, (usuario, nombre_rostro_procesado))
                    conexion.commit()
                    cursor.close()
                    conexion.close()

                    if hasattr(self, 'pantalla_captura'):
                        self.pantalla_captura.destroy()

                    messagebox.showinfo(
                        "✓ Registro Exitoso",
                        f"Usuario: {usuario}\n"
                        f"Imagen: {nombre_rostro_procesado}\n"
                        f"Calidad: {confianza:.0%}\n\n"
                        f"✓ Ya puedes marcar asistencia"
                    )
                    
                except mysql.connector.Error as err:
                    messagebox.showerror("Error BD", f"Error al guardar:\n{err}")
                    if conexion.is_connected():
                        conexion.close()
            else:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")

        except Exception as e:
            messagebox.showerror("Error", f"Error en el registro:\n{str(e)}")
   
   
    def ventana_marcar_asistencia(self):
        self.pantalla_asistencia = Toplevel(self.pantalla)
        self.pantalla_asistencia.title("Marcar Asistencia")
        # 🔹 Tamaño de la ventana
        ancho = 500
        alto = 500
        # 🔹 Tamaño de la pantalla
        pantalla_ancho = self.pantalla_asistencia.winfo_screenwidth()
        pantalla_alto = self.pantalla_asistencia.winfo_screenheight()
        # 🔹 Posición centrada
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        self.pantalla_asistencia.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.pantalla_asistencia.resizable(False, False)
        
        
        Label(self.pantalla_asistencia, text="MARCAR ASISTENCIA",
              bg="#4CAF50", fg="white", width="300", height="2",
              font=("Arial", 12, "bold")).pack()
        
        Label(self.pantalla_asistencia, text="").pack(pady=10)
        
        # Instrucciones
        frame_instrucciones = Frame(self.pantalla_asistencia, bg="#E8F5E9", 
                                   relief=RIDGE, borderwidth=3)
        frame_instrucciones.pack(pady=10, padx=20, fill=BOTH)
        
        Label(frame_instrucciones, text="📸 PREPARACIÓN PARA MARCAR ASISTENCIA:",
              font=("Arial", 11, "bold"), bg="#E8F5E9", fg="#1B5E20").pack(pady=10)
        
        Label(frame_instrucciones, text="✓ CENTRA TU ROSTRO en la cámara",
              font=("Arial", 10, "bold"), bg="#E8F5E9", fg="#2E7D32", anchor="w").pack(padx=20, pady=5)
        
        Label(frame_instrucciones, text="✓ AÑADE BUENA ILUMINACIÓN",
              font=("Arial", 10, "bold"), bg="#E8F5E9", fg="#2E7D32", anchor="w").pack(padx=20, pady=5)
        
        Label(frame_instrucciones, text="✓ Asegúrate de estar registrado previamente",
              font=("Arial", 10), bg="#E8F5E9", anchor="w").pack(padx=20, pady=3)
        
        Label(frame_instrucciones, text="✓ El sistema detectará tu rostro automáticamente",
              font=("Arial", 10), bg="#E8F5E9", anchor="w").pack(padx=20, pady=3)
        
        Label(frame_instrucciones, text="").pack(pady=5)
        
        Label(self.pantalla_asistencia, text="").pack(pady=10)
        
        Button(self.pantalla_asistencia, text="📷 INICIAR CAPTURA", 
               width=30, height=2, bg="#4CAF50", fg="white",
               font=("Arial", 12, "bold"),
               command=self.capturar_asistencia).pack(pady=10)
        
        Button(self.pantalla_asistencia, text="Cancelar", 
               width=30, height=2, bg="#f44336", fg="white",
               font=("Arial", 10),
               command=self.pantalla_asistencia.destroy).pack(pady=5)

    def capturar_asistencia(self):
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
            # 2️⃣ CREAR VENTANA DE VISTA PREVIA
            # ═══════════════════════════════════════════════════════════════
            cv2.namedWindow('Marcar Asistencia', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Marcar Asistencia', 640, 540)

            # ═══════════════════════════════════════════════════════════════
            # 3️⃣ BUCLE PRINCIPAL - SOLO VISTA PREVIA
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
                cv2.ellipse(frame_preview, (center_x, center_y), (axis_x, axis_y), 
                        0, 0, 360, (0, 255, 0), 3)
                
                # ───────────────────────────────────────────────────────────
                # 5️⃣ INTERFAZ SIMPLE
                # ───────────────────────────────────────────────────────────
                # Fondo superior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 0), (640, 70), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                # Título
                cv2.putText(frame_preview, "MARCAR ASISTENCIA", 
                        (180, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame_preview, "Sistema de Reconocimiento Facial", 
                        (160, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                
                # Fondo inferior
                overlay = frame_preview.copy()
                cv2.rectangle(overlay, (0, 500), (640, 540), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame_preview, 0.4, 0, frame_preview)
                
                # Instrucciones
                cv2.putText(frame_preview, "ESPACIO: Capturar  |  ESC: Cancelar", 
                        (140, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                cv2.imshow('Marcar Asistencia', frame_preview)

                # ───────────────────────────────────────────────────────────
                # 6️⃣ CONTROL DE TECLAS
                # ───────────────────────────────────────────────────────────
                tecla = cv2.waitKey(1)
                if tecla == 27:  # ESC
                    break
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
            fecha_hora_str = fecha_hora_actual.strftime("%Y-%m-%d_%H-%M-%S")
            temp_login = f"rostros_asistencia/temp_asistencia_{fecha_hora_str}.jpg"
            cv2.imwrite(temp_login, rostro_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # ═══════════════════════════════════════════════════════════════
            # 1️⃣4️⃣ COMPARAR CON ROSTROS REGISTRADOS
            # ═══════════════════════════════════════════════════════════════
            usuario_encontrado = None

            mejor_distancia = float('inf')  # Cambiado: menor distancia = mejor match
            umbral_distancia = 0.40  # Umbral típico de Facenet512 con cosine
            for archivo in os.listdir("rostros_registro"):
                if archivo.endswith("_rostro.jpg"):
                    distancia = self.comparar_rostros(
                        f"rostros_registro/{archivo}", 
                        temp_login
                    )
                    
                    # Buscar la MENOR distancia (más similar)
                    if distancia < mejor_distancia and distancia < umbral_distancia:
                        mejor_distancia = distancia
                        usuario_encontrado = archivo.replace("_rostro.jpg", "")

            # ───────────────────────────────────────────────────────────
            # 1️⃣5️⃣ VERIFICAR SI SE ENCONTRÓ COINCIDENCIA
            # ───────────────────────────────────────────────────────────
            if usuario_encontrado:
                # Convertir distancia a porcentaje de similitud para mostrar
                similitud_porcentual = max(0, (1 - (mejor_distancia / umbral_distancia)))
                
                fecha_hora_formato_db = fecha_hora_actual.strftime("%Y-%m-%d %H:%M:%S")
                nombre_imagen_asistencia = f"{usuario_encontrado}_{fecha_hora_str}.jpg"
                ruta_imagen_final = f"rostros_asistencia/{nombre_imagen_asistencia}"
                os.rename(temp_login, ruta_imagen_final)

                # [GUARDAR EN BD IGUAL QUE ANTES]
                conexion = self.conectar_db()
                if conexion:
                    try:
                        cursor = conexion.cursor()
                        query = """INSERT INTO asistencias (nombre_usuario, fecha_hora, similitud, imagen_asistencia) 
                                VALUES (%s, %s, %s, %s)"""
                        cursor.execute(query, (usuario_encontrado, fecha_hora_formato_db, 
                                            f"{mejor_distancia:.4f}", nombre_imagen_asistencia))
                        conexion.commit()
                        cursor.close()
                        conexion.close()

                        if hasattr(self, 'pantalla_asistencia'):
                            self.pantalla_asistencia.destroy()

                        messagebox.showinfo(
                            "✓ Asistencia Registrada",
                            f"¡Bienvenido(a) {usuario_encontrado}!\n\n"
                            f"Fecha: {fecha_hora_formato_db}\n"
                            f"Confianza: {similitud_porcentual:.1%}\n"
                            f"Distancia: {mejor_distancia:.3f}\n"
                            f"Calidad: {confianza:.0%}\n"
                            f"Imagen: {nombre_imagen_asistencia}"
                        )
                        
                    except mysql.connector.Error as err:
                        messagebox.showerror("Error BD", f"Error al guardar:\n{err}")
                        if conexion.is_connected():
                            conexion.close()
            else:
                if os.path.exists(temp_login):
                    os.remove(temp_login)
                messagebox.showerror(
                    "✗ Acceso Denegado",
                    f"Rostro no reconocido\n\n"
                    f"Menor distancia encontrada: {mejor_distancia:.3f}\n"
                    f"Umbral requerido: {umbral_distancia:.2f}\n\n"
                    f"Si no estás registrado, regístrate primero"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Error al marcar asistencia:\n{str(e)}")

    def comparar_rostros(self, img1_path, img2_path):
        """
        Compara dos rostros y retorna la DISTANCIA (menor = más similar)
        """
        try:
            if not os.path.exists(img1_path) or not os.path.exists(img2_path):
                return float('inf')
            
            resultado = DeepFace.verify(
                img1_path=img1_path,
                img2_path=img2_path,
                model_name='Facenet512',
                detector_backend='skip',
                distance_metric='cosine',
                enforce_detection=False  # No fallar si no detecta rostro
            )
            
            # Retornar solo la distancia (DeepFace ya la calcula bien)
            return resultado['distance']
            
        except Exception as e:
            print(f"Error DeepFace: {e}")
            # Fallback a ORB
            similitud_orb = self.comparar_rostros_orb(img1_path, img2_path)
            # Convertir similitud ORB (0-1) a distancia (1-0)
            return 1.0 - similitud_orb
        
    def comparar_rostros_orb(self, img1_path, img2_path):
        """
        Fallback con ORB - retorna similitud (0-1)
        """
        try:
            img1 = cv2.imread(img1_path, 0)
            img2 = cv2.imread(img2_path, 0)
            
            if img1 is None or img2 is None:
                return 0.0
            
            orb = cv2.ORB_create(nfeatures=2000)  # Más features = mejor precisión
            
            kp1, desc1 = orb.detectAndCompute(img1, None)
            kp2, desc2 = orb.detectAndCompute(img2, None)
            
            if desc1 is None or desc2 is None:
                return 0.0
            
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(desc1, desc2)
            
            if len(matches) == 0:
                return 0.0
            
            # Ordenar por distancia y tomar los mejores matches
            matches = sorted(matches, key=lambda x: x.distance)
            buenos_matches = [m for m in matches[:100] if m.distance < 50]
            
            similitud = len(buenos_matches) / min(100, len(matches))
            return similitud
            
        except Exception as e:
            print(f"Error ORB: {e}")
            return 0.0
    
    def iniciar(self):
        self.pantalla.mainloop()

# Ejecutar el sistema
if __name__ == "__main__":
    sistema = SistemaAsistencia()
    sistema.iniciar()