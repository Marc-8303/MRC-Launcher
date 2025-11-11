import minecraft_launcher_lib
import subprocess
import os
import requests
import json
import queue
import shutil
import threading
from tkinter import filedialog
import customtkinter
from PIL import Image
from functools import partial

""""
Datos globales
Estas variables almacenan el estado de la aplicación para no tener que pasarlas constantemente

Launcher creado por zkannek12 (Marcelo R) - 2025
"""

CONFIG_FILE = "config.json"
MINECRAFT_DIRECTORY = ""

def save_configuration(username, skin_path):
    """
    Que hace?

    Guarda la configuración actual (usuario y skin) en el archivo JSON.
    """
    config = {"last_username": username, "last_skin_path": skin_path}
    try:
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving configuration: {e}")

def load_configuration():
    """
    Que hace?
    
    Carga la configuración desde el archivo JSON si existe.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}
    return {}

def load_initial_data():
    """
    Que hace?
    
    Se encarga de crear el directorio de Minecraft si no existe y de cargar
    la lista de versiones para mostrar en la UI.
    """
    global MINECRAFT_DIRECTORY
    
    try:
        MINECRAFT_DIRECTORY = minecraft_launcher_lib.utils.get_minecraft_directory()

        if not os.path.exists(MINECRAFT_DIRECTORY):
            os.makedirs(os.path.join(MINECRAFT_DIRECTORY, "resourcepacks"), exist_ok=True)
        all_versions = minecraft_launcher_lib.utils.get_version_list()
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIRECTORY)
        installed_ids = {v['id'] for v in installed_versions}
        return all_versions, installed_ids
    except Exception as e:
        print(f"Error loading initial data: {e}")
        return [], set()

def _populate_versions_in_batches(scroll_frame, version_variable, versions_to_add, loading_label, index=0):
    BATCH_SIZE = 10
    count = 0
    while count < BATCH_SIZE and index < len(versions_to_add):
        version = versions_to_add[index]
        radio_button = customtkinter.CTkRadioButton(master=scroll_frame, text=version, variable=version_variable, value=version)
        radio_button.pack(fill="x", padx=10, pady=5)
        count += 1
        index += 1
    if index < len(versions_to_add):
        scroll_frame.after(10, partial(_populate_versions_in_batches, scroll_frame, version_variable, versions_to_add, loading_label, index))
    else:
        loading_label.destroy()
        if versions_to_add:
            version_variable.set(versions_to_add[0])

def update_version_list(ui_elements, all_versions, installed_ids):
    """
    Limpia y vuelve a llenar la lista de versiones en la UI, basándose
    en el estado del checkbox de snapshots.
    """
    version_scroll_frame = ui_elements["version_scroll_frame"]
    show_snapshots = ui_elements["show_snapshots_checkbox"].get() == 1
    version_variable = ui_elements["version_variable"]

    for widget in version_scroll_frame.winfo_children():
        widget.destroy()
    loading_label = customtkinter.CTkLabel(master=version_scroll_frame, text="Loading versions...")
    loading_label.pack(pady=20)
    display_versions = []

    for version in all_versions:
        version_id = version['id']
        is_release = version['type'] == 'release'
        if is_release or show_snapshots:
            if version_id in installed_ids:
                display_versions.append(f"{version_id} (Installed)")
            else:
                display_versions.append(version_id)
    if not display_versions:
        loading_label.configure(text="No versions found.")
        return
    _populate_versions_in_batches(version_scroll_frame, version_variable, display_versions, loading_label)

def _create_skin_preview_image(path, size):
    """
    Que hace?
    
    Función auxiliar 'privada' para crear una imagen de preview compatible con CTkinter.
    Ahora usa CTkImage para un escalado correcto en pantallas HighDPI.
    """
    try:
        pillow_image = Image.open(path)
        return customtkinter.CTkImage(light_image=pillow_image, dark_image=pillow_image, size=size)
    except Exception as e:
        print(f"Error creating preview image: {e}")
        return None
    

def create_skin_resource_pack(skin_path):
    """
    Que hace?

    Crea un paquete de recursos .zip con la skin proporcionada.
    """
    pack_name = "MRC_Launcher_Skin"
    temp_pack_dir = "temp_pack_dir"

    if os.path.exists(temp_pack_dir): shutil.rmtree(temp_pack_dir)
    try:
        steve_path = os.path.join(temp_pack_dir, "assets", "minecraft", "textures", "entity")
        os.makedirs(steve_path, exist_ok=True)
        mcmeta = {"pack": {"pack_format": 15, "description": "Custom skin for MRC Launcher"}}
        with open(os.path.join(temp_pack_dir, "pack.mcmeta"), "w") as f: json.dump(mcmeta, f, indent=4)
        shutil.copy(skin_path, os.path.join(steve_path, "steve.png"))
        shutil.copy(skin_path, os.path.join(steve_path, "alex.png"))
        zip_path = os.path.join(MINECRAFT_DIRECTORY, "resourcepacks", pack_name)
        shutil.make_archive(zip_path, 'zip', temp_pack_dir)
        return True
    except Exception as e:
        print(f"Error creating skin resource pack: {e}")
        return False
    finally:
        if os.path.exists(temp_pack_dir): shutil.rmtree(temp_pack_dir)

def enable_skin_resource_pack():
    """
    Que hace?
    
    Modifica options.txt para activar nuestro paquete de recursos.
    """
    options_file = os.path.join(MINECRAFT_DIRECTORY, "options.txt")
    pack_name = "file/MRC_Launcher_Skin.zip"

    try:
        if not os.path.exists(options_file):
            with open(options_file, "w") as f: f.write(f'resourcePacks:{json.dumps([pack_name])}\n')
            return
        with open(options_file, "r") as f: lines = f.readlines()
        new_lines = []
        pack_found = False
        for line in lines:
            if line.startswith("resourcePacks:"):
                current_packs = json.loads(line.split(":", 1)[1].strip())
                if pack_name not in current_packs: current_packs.insert(0, pack_name)
                new_lines.append(f'resourcePacks:{json.dumps(current_packs)}\n')
                pack_found = True
            else:
                new_lines.append(line)
        if not pack_found: new_lines.append(f'resourcePacks:{json.dumps([pack_name])}\n')
        with open(options_file, "w") as f: f.writelines(new_lines)
    except Exception as e:
        print(f"Could not enable skin resource pack: {e}")

def select_and_process_skin(ui_elements):
    """
    Que hace?
    
    Abre el diálogo de archivo, procesa la skin y actualiza la UI.
    """
    skin_path = filedialog.askopenfilename(title="Select your skin", filetypes=[("PNG Files", "*.png")])
    if skin_path:
        if create_skin_resource_pack(skin_path):
            enable_skin_resource_pack()
            preview_label = ui_elements["skin_preview_label"]
            new_preview = _create_skin_preview_image(skin_path, (64, 64))
            if new_preview:
                preview_label.configure(image=new_preview, text="")
                preview_label.image = new_preview
            save_configuration(ui_elements["username_entry"].get(), skin_path)
        else:
            ui_elements["status_label"].configure(text="Error processing skin.", text_color="red")

def update_ram_label(value, ram_label):
    """
    Que hace?
    
    Actualiza la etiqueta de la RAM cuando se mueve el slider.
    """
    ram_in_mb = int(value)
    ram_label.configure(text=f"Custom RAM Allocation: {ram_in_mb} MB")

def _launch_game_in_thread(minecraft_command, update_queue):
    """
    Que hace?

    Esta función se ejecuta en un hilo separado y pone mensajes en la cola.
    """
    try:
        subprocess.run(minecraft_command)
        update_queue.put("GAME_CLOSED")
    except Exception as e:
        print(f"An error occurred in the game thread: {e}")
        update_queue.put(f"ERROR:{e}")

def process_queue_updates(app, status_label, update_queue):
    """
    Que hace?

    Revisa la cola en busca de mensajes y actualiza la UI de forma segura.
    """
    try:
        message = update_queue.get_nowait()
        if message == "GAME_CLOSED":
            status_label.configure(text="Game closed. Ready to play again!", text_color="green")
        elif message.startswith("ERROR:"):
            error_details = message.split(":", 1)[1]
            status_label.configure(text=f"Error launching: {error_details}", text_color="red")
    except queue.Empty:
        pass
    finally:
        app.after(100, lambda: process_queue_updates(app, status_label, update_queue))

def launch_or_install_minecraft(ui_elements, all_versions, installed_ids):
    """
    Que hace?
    
    Función principal del botón "Jugar / Instalar". Ahora usa un hilo para lanzar el juego.
    """

    app = ui_elements["app"]

    username_entry = ui_elements["username_entry"]
    version_variable = ui_elements["version_variable"]

    ram_slider = ui_elements["ram_slider"]
    java_entry = ui_elements["java_entry"]

    status_label = ui_elements["status_label"]

    username = username_entry.get()
    selected_display_version = version_variable.get()
    ram_mb = int(ram_slider.get())
    if not username:
        status_label.configure(text="Error: Username cannot be empty.", text_color="red")
        return
    version_id = selected_display_version.replace(" (Installed)", "")
    if "Error" in version_id or not version_id:
        status_label.configure(text="Error: No valid version selected.", text_color="red")
        return
    config = load_configuration()
    save_configuration(username, config.get("last_skin_path", ""))

    if version_id not in installed_ids:
        try:
            status_label.configure(text=f"Installing {version_id}, please wait...", text_color="yellow")
            app.update_idletasks()
            minecraft_launcher_lib.install.install_minecraft_version(version_id, MINECRAFT_DIRECTORY)
            installed_ids.add(version_id)
            status_label.configure(text=f"{version_id} installed successfully!", text_color="green")
            update_version_list(ui_elements, all_versions, installed_ids)
            app.update_idletasks()
        except Exception as e:
            status_label.configure(text=f"Error during installation: {e}", text_color="red")
            return
            
    options = {"username": username, "uuid": "", "token": "", "jvmArguments": [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"]}
    java_args = java_entry.get()
    if java_args:
        options["jvmArguments"].extend(java_args.split())
    try:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version_id, MINECRAFT_DIRECTORY, options)
        status_label.configure(text=f"Launching Minecraft {version_id}...", text_color="green")
        
        update_queue = queue.Queue()
        game_thread = threading.Thread(target=_launch_game_in_thread, args=(minecraft_command, update_queue))
        game_thread.start()
        
        app.after(100, lambda: process_queue_updates(app, status_label, update_queue))

    except Exception as e:
        status_label.configure(text=f"Error preparing launch: {e}", text_color="red")