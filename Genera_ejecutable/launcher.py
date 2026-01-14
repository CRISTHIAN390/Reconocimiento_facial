import os
import sys
import subprocess

def main():
    # Ruta del proyectos
    PROJECT_DIR = r"ruta de los archivos"    #"C:\Reconocimiento_facial"
    
    # Ruta del venv
    VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "Scripts", "pythonw.exe")
    
    # Archivo principal a ejecutar
    MAIN_SCRIPT = os.path.join(PROJECT_DIR, "Login_Vision.py")
    
    
    # Verificar que existe el venv
    if not os.path.exists(VENV_PYTHON):
        print(f"[ERROR] No se encontró el entorno virtual en:")
        print(f"  {VENV_PYTHON}")
        print()
        print("Solución: Ejecuta en cmd:")
        print(f"  cd {PROJECT_DIR}")
        print("  python -m venv venv")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    # Verificar que existe el script principal
    if not os.path.exists(MAIN_SCRIPT):
        print(f"[ERROR] No se encontró Login_Vision.py en:")
        print(f"  {MAIN_SCRIPT}")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    print("[OK] Entorno virtual encontrado")
    print("[OK] Iniciando aplicación...")
    print()
    
    # Cambiar al directorio del proyecto
    os.chdir(PROJECT_DIR)
    
    # Ejecutar el script con el Python del venv
    try:
        subprocess.run([VENV_PYTHON, MAIN_SCRIPT], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] La aplicación cerró con código de error: {e.returncode}")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Aplicación cerrada por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()
    
    

#pyinstaller --onefile --windowed --name="Sistema_Asistencia" --icon="icono.ico" launcher.py
#pip install pyinstaller      