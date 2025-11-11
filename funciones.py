import os
import sys
import subprocess
import shutil
import json
import threading
import queue
from functools import partial

import minecraft_launcher_lib
import google.generativeai as genai
import customtkinter as ctk  


def get_app_data_dir():
    """Obtiene la ruta al directorio de datos de la aplicación de forma multiplataforma."""
    APP_NAME = "MCLauncher"

    if sys.platform == "win32":
        app_data_path = os.getenv("APPDATA")
    elif sys.platform == "darwin":
        app_data_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        app_data_path = os.path.join(os.path.expanduser("~"), ".config")

    launcher_data_dir = os.path.join(app_data_path, APP_NAME)
    os.makedirs(launcher_data_dir, exist_ok=True)

    return launcher_data_dir


APP_DATA_DIR = get_app_data_dir()
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
SKIN_PACK_NAME = "MCL_Launcher_Skin"

_mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
MINECRAFT_DIRECTORY = _mc_dir if _mc_dir else ""

def load_configuration():
    """Carga el archivo de configuración si existe, devuelve un dict vacío en error."""
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, IOError):
        return {}


def save_configuration(config_data):
    """Guarda el diccionario de configuración en disco."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

    except Exception as e:
        print(f"Error al guardar la configuración: {e}")


def load_initial_data():
    """Prepara carpetas y devuelve (all_versions, installed_ids)."""
    try:
        os.makedirs(os.path.join(MINECRAFT_DIRECTORY, "resourcepacks"), exist_ok=True)

        all_versions = minecraft_launcher_lib.utils.get_version_list()

        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIRECTORY)
        installed_ids = {v["id"] for v in installed_versions}

        return all_versions, installed_ids

    except Exception as e:
        print(f"Error al cargar datos iniciales: {e}")
        return [], set()


def delete_all_user_data():
    """Elimina el archivo de configuración y el paquete de skin si existen."""
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
        except OSError as e:
            print(f"Error al eliminar '{CONFIG_FILE}': {e}")

    skin_pack_path = os.path.join(MINECRAFT_DIRECTORY, "resourcepacks", f"{SKIN_PACK_NAME}.zip")

    if os.path.exists(skin_pack_path):
        try:
            os.remove(skin_pack_path)
        except OSError as e:
            print(f"Error al eliminar el paquete de skin: {e}")


def open_directory(path_to_open):
    """Abre un directorio en el explorador de archivos. Devuelve (éxito, mensaje)."""
    if not os.path.exists(path_to_open):
        return False, f"Directory '{os.path.basename(path_to_open)}' not found."

    try:
        if sys.platform == "win32":
            os.startfile(path_to_open)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path_to_open])
        else:
            subprocess.Popen(["xdg-open", path_to_open])

        return True, f"Opened '{os.path.basename(path_to_open)}' directory."

    except Exception as e:
        return False, f"Error opening directory: {e}"


def _get_pack_format(version_id: str) -> int:
    """Determina el pack_format correcto basado en el ID de la versión de Minecraft."""
    clean_version = version_id.replace(" (Installed)", "").strip()

    try:
        parts = clean_version.split('.')
        version_tuple = tuple(map(int, parts[:2]))
    except ValueError:
        return 15

    if version_tuple >= (1, 20):
        if '1.20.3' in clean_version or '1.20.4' in clean_version:
            return 22

        if '1.20.2' in clean_version:
            return 18

        return 15

    if version_tuple == (1, 19):
        if '1.19.4' in clean_version:
            return 13

        if '1.19.3' in clean_version:
            return 12

        return 9

    if version_tuple == (1, 18):
        return 8

    if version_tuple == (1, 17):
        return 7

    if version_tuple >= (1, 15):
        return 5

    if version_tuple >= (1, 13):
        return 4

    if version_tuple >= (1, 11):
        return 3

    if version_tuple >= (1, 9):
        return 2

    return 1


def create_skin_resource_pack(skin_path: str, version_id: str):
    """Crea un paquete de recursos temporal con la skin y lo comprime en resourcepacks."""
    temp_pack_dir = "temp_pack_dir"

    if os.path.exists(temp_pack_dir):
        shutil.rmtree(temp_pack_dir)

    try:
        pack_format = _get_pack_format(version_id)

        entity_path = os.path.join(temp_pack_dir, "assets", "minecraft", "textures", "entity")
        os.makedirs(entity_path, exist_ok=True)

        mcmeta = {
            "pack": {
                "pack_format": pack_format,
                "description": "Custom skin for MCL Launcher",
            }
        }

        with open(os.path.join(temp_pack_dir, "pack.mcmeta"), "w", encoding="utf-8") as f:
            json.dump(mcmeta, f, indent=4)

        shutil.copy(skin_path, os.path.join(entity_path, "steve.png"))
        shutil.copy(skin_path, os.path.join(entity_path, "alex.png"))

        zip_path = os.path.join(MINECRAFT_DIRECTORY, "resourcepacks", SKIN_PACK_NAME)
        shutil.make_archive(zip_path, 'zip', temp_pack_dir)

        return True

    except Exception as e:
        print(f"Error al crear el paquete de recursos: {e}")
        return False

    finally:
        if os.path.exists(temp_pack_dir):
            shutil.rmtree(temp_pack_dir)


def enable_skin_resource_pack():
    """Inserta (o mueve al inicio) el paquete de skin dentro de options.txt como resourcePack."""
    options_file = os.path.join(MINECRAFT_DIRECTORY, "options.txt")
    pack_name = f"file/{SKIN_PACK_NAME}.zip"

    try:
        if not os.path.exists(options_file):
            with open(options_file, "w", encoding="utf-8") as f:
                f.write(f'resourcePacks:{json.dumps([pack_name])}\n')

            return

        with open(options_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        pack_found = False

        for line in lines:
            if line.strip().startswith("resourcePacks:"):
                current_packs = json.loads(line.split(":", 1)[1].strip())

                if pack_name in current_packs:
                    current_packs.remove(pack_name)

                current_packs.insert(0, pack_name)
                new_lines.append(f'resourcePacks:{json.dumps(current_packs)}\n')
                pack_found = True
            else:
                new_lines.append(line)

        if not pack_found:
            new_lines.append(f'resourcePacks:{json.dumps([pack_name])}\n')

        with open(options_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    except Exception as e:
        print(f"No se pudo activar el paquete de recursos: {e}")


def process_skin(skin_path, version_id):
    """Crea y activa el paquete de recursos de la skin. Devuelve (éxito, mensaje)."""
    if not skin_path or not version_id:
        return False, "Skin path or version ID is missing."

    if create_skin_resource_pack(skin_path, version_id):
        enable_skin_resource_pack()
        return True, "Offline skin updated successfully!"

    return False, "Error processing skin."

def call_ia_api_in_thread(prompt, api_key, result_queue):
    """Función para un hilo. Llama a la API de IA y pone el resultado en una cola."""
    resultados, error = obtener_sugerencias_ia_desde_api(prompt, api_key)
    if error:
        result_queue.put(("ERROR", error))
    else:
        result_queue.put(("SUCCESS", resultados))


def obtener_sugerencias_ia_desde_api(prompt_usuario, api_key):
    """Se conecta a la API de Google Gemini para obtener sugerencias."""
    try:
        if not api_key:
            return None, "Google API Key not found."

        genai.configure(api_key=api_key)

        system_prompt = (
            "You are a helpful assistant for a Minecraft launcher. "
            "You must respond ONLY with a valid JSON array of objects. "
            "Each object must have five keys: 'name', 'description', 'url', 'loader', and 'version'."
        )

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(system_prompt + "\n\nUser request: " + prompt_usuario)

        cleaned_response = (
            response.text.strip().replace("```json", "").replace("```", "").strip()
        )

        return json.loads(cleaned_response), None

    except json.JSONDecodeError:
        return None, "AI returned an invalid format."

    except Exception as e:
        if "API_KEY_INVALID" in str(e):
            return None, "The provided API Key is invalid."

        return None, str(e)


def _populate_versions_in_batches(scroll_frame, version_variable, versions_to_add, loading_label, index=0):
    """Agrega versiones por lotes al scroll_frame para no bloquear la UI."""
    BATCH_SIZE = 10
    count = 0

    while count < BATCH_SIZE and index < len(versions_to_add):
        version = versions_to_add[index]
        ctk.CTkRadioButton(
            master=scroll_frame, text=version, variable=version_variable, value=version
        ).pack(fill="x", padx=10, pady=5)

        count += 1
        index += 1

    if index < len(versions_to_add):
        scroll_frame.after(
            10,
            partial(
                _populate_versions_in_batches,
                scroll_frame,
                version_variable,
                versions_to_add,
                loading_label,
                index,
            ),
        )

    else:
        loading_label.destroy()

        if versions_to_add:
            version_variable.set(versions_to_add[0])


def update_version_list(ui_elements, all_versions, installed_ids):
    """Actualiza la lista de versiones en la UI."""
    scroll_frame = ui_elements["version_scroll_frame"]
    show_snapshots = ui_elements["show_snapshots_checkbox"].get() == 1
    version_var = ui_elements["version_variable"]

    for widget in scroll_frame.winfo_children():
        widget.destroy()

    loading_label = ctk.CTkLabel(master=scroll_frame, text="Loading versions...")
    loading_label.pack(pady=20)

    display_versions = [
        f"{v['id']} (Installed)" if v["id"] in installed_ids else v["id"]
        for v in all_versions
        if v["type"] == "release" or show_snapshots
    ]

    if not display_versions:
        loading_label.configure(text="No versions found.")
        return

    _populate_versions_in_batches(scroll_frame, version_var, display_versions, loading_label)


def bind_version_change(ui_elements, selected_label):
    """Vincula el cambio de la variable de versión a la actualización de una etiqueta."""
    version_var = ui_elements.get("version_variable")

    def _on_change(*args):
        sel = version_var.get()
        selected_label.configure(text=f"Selected Version: {sel}" if sel else "Selected Version: None")

    version_var.trace_add("write", _on_change)
    _on_change()


def _launch_game_in_thread(minecraft_command, update_queue):
    try:
        subprocess.run(minecraft_command)
        update_queue.put("GAME_CLOSED")
    except Exception as e:
        update_queue.put(f"ERROR:{e}")


def process_queue_updates(app, status_label, update_queue):
    try:
        message = update_queue.get_nowait()

        if message == "GAME_CLOSED":
            status_label.configure(text="Game closed. Ready to play again!", text_color="green")

        elif message.startswith("ERROR:"):
            status_label.configure(text=f"Error launching: {message.split(':', 1)[1]}", text_color="red")

    except queue.Empty:
        pass

    finally:
        app.after(100, lambda: process_queue_updates(app, status_label, update_queue))


def launch_or_install_minecraft(ui_elements, all_versions, installed_ids):
    app = ui_elements["app"]
    status_label = ui_elements["status_label"]

    version_id = ui_elements["version_variable"].get().replace(" (Installed)", "")
    username = ui_elements["username_entry"].get()

    if not version_id:
        status_label.configure(text="Error: No valid version selected.", text_color="red")
        return

    if not username:
        status_label.configure(text="Error: Username cannot be empty.", text_color="red")
        return

    config = load_configuration()
    config["last_username"] = username
    save_configuration(config)

    if version_id not in installed_ids:
        try:
            status_label.configure(text=f"Installing {version_id}...", text_color="yellow")
            app.update_idletasks()

            minecraft_launcher_lib.install.install_minecraft_version(version_id, MINECRAFT_DIRECTORY)

            installed_ids.add(version_id)
            update_version_list(ui_elements, all_versions, installed_ids)

            status_label.configure(text=f"{version_id} installed!", text_color="green")
            app.update_idletasks()

        except Exception as e:
            status_label.configure(text=f"Installation Error: {e}", text_color="red")
            return

    try:
        ram_mb = config.get("ram_mb", 512)
        jvm_args_extra = config.get("jvm_args", "")

        options = {
            "username": username,
            "uuid": "",
            "token": "",
            "jvmArguments": [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"],
        }

        if jvm_args_extra:
            options["jvmArguments"].extend(jvm_args_extra.split())

        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
            version_id, MINECRAFT_DIRECTORY, options
        )

        status_label.configure(text=f"Launching Minecraft {version_id}...", text_color="green")

        update_queue = queue.Queue()

        threading.Thread(
            target=_launch_game_in_thread,
            args=(minecraft_command, update_queue),
            daemon=True,
        ).start()

        app.after(100, lambda: process_queue_updates(app, status_label, update_queue))

    except Exception as e:
        status_label.configure(text=f"Launch Error: {e}", text_color="red")
