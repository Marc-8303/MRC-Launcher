import minecraft_launcher_lib
import subprocess
import os
import json
import shutil
import threading
from tkinter import filedialog
import customtkinter
from PIL import Image

""""
Datos globales
Estas variables almacenan el estado de la aplicación para no tener que pasarlas constantemente

Launcher creado por zkannek12 (Marcelo R) - 2025
"""
CONFIG_FILE = "config.json"
MINECRAFT_DIRECTORY = ""
INSTALLED_VERSION_IDS = set()


def guardar_configuracion(username, skin_path):
    """
    Que hace?

    Guarda la configuración actual (usuario y skin) en el archivo JSON.
    """
    config = {"last_username": username, "last_skin_path": skin_path}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error al guardar la configuración: {e}")

def cargar_configuracion():
    """
    Que hace?
    
    Carga la configuración desde el archivo JSON si existe.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            return {}
    return {}

def load_initial_data():
    """
    Que hace?
    
    Se encarga de crear el directorio de Minecraft si no existe y de cargar
    la lista de versiones para mostrar en la UI.
    """
    global MINECRAFT_DIRECTORY, INSTALLED_VERSION_IDS
    try:
        MINECRAFT_DIRECTORY = minecraft_launcher_lib.utils.get_minecraft_directory()
        if not os.path.exists(MINECRAFT_DIRECTORY):
            os.makedirs(MINECRAFT_DIRECTORY)
            os.makedirs(os.path.join(MINECRAFT_DIRECTORY, "resourcepacks"), exist_ok=True)

        all_versions = minecraft_launcher_lib.utils.get_version_list()
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIRECTORY)
        
        INSTALLED_VERSION_IDS = {v['id'] for v in installed_versions}

        display_versions = []
        for version in all_versions:
            if version['type'] == 'release':
                version_id = version['id']
                if version_id in INSTALLED_VERSION_IDS:
                    display_versions.append(f"{version_id} (Installed)")
                else:
                    display_versions.append(version_id)
        return display_versions
    except Exception as e:
        print(f"Error cargando datos iniciales: {e}")
        return [f"Error al buscar: {e}"]


def _create_skin_preview_image(path, size):
    """
    Que hace?
    
    Función auxiliar 'privada' para crear una imagen de preview compatible con CTkinter.
    Ahora usa CTkImage para un escalado correcto en pantallas HighDPI.
    """
    try:
        pillow_image = Image.open(path)
        
        ctk_image = customtkinter.CTkImage(
            light_image=pillow_image,
            dark_image=pillow_image, 
            size=size
        )
        return ctk_image
    except Exception as e:
        print(f"Error al crear la imagen de preview: {e}")
        return None

def crear_paquete_de_skin(skin_path):
    """
    Que hace?

    Crea un paquete de recursos .zip con la skin proporcionada.
    """
    pack_name = "MRC_Launcher_Skin"
    temp_pack_dir = os.path.join("temp_pack_dir")

    if os.path.exists(temp_pack_dir):
        shutil.rmtree(temp_pack_dir)
    
    try:
        steve_path = os.path.join(temp_pack_dir, "assets", "minecraft", "textures", "entity")
        os.makedirs(steve_path, exist_ok=True)

        mcmeta_content = {
            "pack": {
                "pack_format": 15, 
                "description": "Skin personalizada para MRC Launcher"
            }
        }
        with open(os.path.join(temp_pack_dir, "pack.mcmeta"), "w") as f:
            json.dump(mcmeta_content, f, indent=4)
        
        shutil.copy(skin_path, os.path.join(steve_path, "steve.png"))
        shutil.copy(skin_path, os.path.join(steve_path, "alex.png"))

        zip_output_path = os.path.join(MINECRAFT_DIRECTORY, "resourcepacks", pack_name)
        shutil.make_archive(zip_output_path, 'zip', temp_pack_dir)
        
        print(f"Paquete de skin creado/actualizado en: {zip_output_path}.zip")
        return True
    except Exception as e:
        print(f"Error creando el paquete de skin: {e}")
        return False
    finally:
        if os.path.exists(temp_pack_dir):
            shutil.rmtree(temp_pack_dir)

def activar_paquete_de_skin():
    """
    Que hace?
    
    Modifica options.txt para activar nuestro paquete de recursos.
    """
    options_file = os.path.join(MINECRAFT_DIRECTORY, "options.txt")
    pack_name = "file/MRC_Launcher_Skin.zip"
    
    try:
        if not os.path.exists(options_file):
            with open(options_file, "w") as f:
                f.write(f'resourcePacks:{json.dumps([pack_name])}\n')
            return

        with open(options_file, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        pack_found = False
        for line in lines:
            if line.startswith("resourcePacks:"):
                import re
                current_packs_str = line.split(":", 1)[1].strip()
                current_packs = json.loads(current_packs_str)
                if pack_name not in current_packs:
                    current_packs.insert(0, pack_name)
                new_line = f'resourcePacks:{json.dumps(current_packs)}\n'
                new_lines.append(new_line)
                pack_found = True
            else:
                new_lines.append(line)
        
        if not pack_found:
             new_lines.append(f'resourcePacks:{json.dumps([pack_name])}\n')
        
        with open(options_file, "w") as f:
            f.writelines(new_lines)
        print("Paquete de skin activado en options.txt")
    except Exception as e:
        print(f"No se pudo activar el paquete de skin en options.txt: {e}")

def seleccionar_y_procesar_skin(ui_elements):
    """
    Que hace?
    
    Abre el diálogo de archivo, procesa la skin y actualiza la UI.
    """
    skin_path = filedialog.askopenfilename(
        title="Selecciona tu skin",
        filetypes=[("Archivos PNG", "*.png")]
    )
    if skin_path:
        if crear_paquete_de_skin(skin_path):
            activar_paquete_de_skin()
            
            preview_label = ui_elements["skin_preview_label"]
            new_preview_image = _create_skin_preview_image(skin_path, (128, 128))
            if new_preview_image:
                preview_label.configure(image=new_preview_image, text="")
                preview_label.image = new_preview_image
            
            guardar_configuracion(ui_elements["username_entry"].get(), skin_path)
            print("Skin procesada y guardada.")
        else:
            ui_elements["status_label"].configure(text="Error al procesar la skin.", text_color="red")

def actualizar_label_ram(valor, label_ram):
    """
    Que hace?
    
    Actualiza la etiqueta de la RAM cuando se mueve el slider.
    """
    ram_en_mb = int(valor)
    label_ram.configure(text=f"Custom RAM Allocation: {ram_en_mb} MB")

def _lanzar_juego_en_hilo(minecraft_command, ui_elements):
    """
    Esta función se ejecuta en un hilo separado para no bloquear la UI.
    Contiene la llamada bloqueante a subprocess.run().
    """
    try:
        subprocess.run(minecraft_command)
        
        # Una vez que el juego se cierra, actualizamos la UI de forma segura
        ui_elements["app"].after(0, lambda: ui_elements["status_label"].configure(
            text="El juego se ha cerrado. ¡Listo para jugar de nuevo!", text_color="green"))
            
    except Exception as e:
        print(f"Ocurrió un error en el hilo del juego: {e}")
        ui_elements["app"].after(0, lambda: ui_elements["status_label"].configure(
            text=f"Error al lanzar: {e}", text_color="red"))

def lanzar_o_instalar_minecraft(ui_elements):
    """
    Función principal del botón "Jugar / Instalar". Ahora usa un hilo para lanzar el juego.
    """
    app = ui_elements["app"]
    username_entry = ui_elements["username_entry"]
    version_variable = ui_elements["version_variable"]
    slider_ram = ui_elements["slider_ram"]
    java_entry = ui_elements["java_entry"]
    status_label = ui_elements["status_label"]

    usuario = username_entry.get()
    selected_display_version = version_variable.get()
    ram_mb = int(slider_ram.get())

    if not usuario:
        status_label.configure(text="Error: El nombre de usuario no puede estar vacío.", text_color="red")
        return
        
    version_id = selected_display_version.replace(" (Installed)", "")

    if "Error al buscar" in version_id:
        status_label.configure(text="Error: No se ha podido cargar la lista de versiones.", text_color="red")
        return
    
    config = cargar_configuracion()
    guardar_configuracion(usuario, config.get("last_skin_path", ""))

    if version_id not in INSTALLED_VERSION_IDS:
        try:
            status_label.configure(text=f"Instalando {version_id}, por favor espera...", text_color="yellow")
            app.update_idletasks()
            minecraft_launcher_lib.install.install_minecraft_version(version_id, MINECRAFT_DIRECTORY)
            INSTALLED_VERSION_IDS.add(version_id)
            status_label.configure(text=f"¡{version_id} instalado con éxito!", text_color="green")
            app.update_idletasks()
        except Exception as e:
            status_label.configure(text=f"Error durante la instalación: {e}", text_color="red")
            return

    options = {
        "username": usuario, "uuid": "", "token": "",
        "jvmArguments": [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"]
    }
    java_args = java_entry.get()
    if java_args:
        options["jvmArguments"].extend(java_args.split())

    try:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version_id, MINECRAFT_DIRECTORY, options)
        
        status_label.configure(text=f"Launching Minecraft {version_id}...", text_color="green")
        
        game_thread = threading.Thread(target=_lanzar_juego_en_hilo, args=(minecraft_command, ui_elements))
        game_thread.start()
        
    except Exception as e:
        status_label.configure(text=f"Error al preparar el lanzamiento: {e}", text_color="red")
