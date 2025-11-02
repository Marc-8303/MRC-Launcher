import customtkinter
import launcher_logic
import os
import sys

"""
MRC Launcher - Minecraft Resourceful Client Launcher
Launcher creado por zkannek12 (Marcelo R) - 2025

Este launcher fue creado con el fin de ser simple, ligero y funcional,
permitiendo a los usuarios jugar a Minecraft con facilidad.

Si lees esto supongo que te interesa el proyecto, asi que gracias!
si encuentras algun error reportalo en el github!

aqui voy a explicar brevemente con # ya que es UI, en el otro py 
es con corchetas pues es mas densa la explicacion

"""

# Configuracion default UI
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

app = customtkinter.CTk()
app.geometry("600x920")
app.title("MRC Launcher")
app.resizable(False, False)

# para cargar el icono de la app
try:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, "assets/logo.ico")
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)
    else:
        print(f"Warning: Icon file not found at: {icon_path}")
except Exception as e:
    print(f"Could not load icon: {e}")

# cargamos el data inicial(si hay) y la configuracion
ALL_VERSIONS, INSTALLED_IDS = launcher_logic.load_initial_data()
config = launcher_logic.load_configuration()
last_username = config.get("last_username", "")
last_skin_path = config.get("last_skin_path", "")

# LAYOUT DEL UI APP

# header
header_frame = customtkinter.CTkFrame(master=app)
header_frame.pack(pady=10, padx=60, fill="x")
main_title = customtkinter.CTkLabel(master=header_frame, text="MRC Launcher", font=("monocraft", 24))
main_title.pack(pady=12, padx=10)

# body
setup_options_label = customtkinter.CTkLabel(master=app, text="Setup Options:", font=("jetbrains mono", 16))
setup_options_label.pack(pady=0, padx=10)

# Body - Frame 1 (pedimos nombre usuario y version)
user_version_frame = customtkinter.CTkFrame(master=app)
user_version_frame.pack(pady=10, padx=60, fill="x")
username_label = customtkinter.CTkLabel(master=user_version_frame, text="Minecraft Username:", font=("jetbrains mono", 14))
username_entry = customtkinter.CTkEntry(master=user_version_frame, width=300)
username_entry.insert(0, last_username)
username_label.grid(row=0, column=0, padx=10, pady=20, sticky="w")
username_entry.grid(row=0, column=1, padx=10, pady=20, sticky="ew")
version_select_label = customtkinter.CTkLabel(master=user_version_frame, text="Select Minecraft Version:", font=("jetbrains mono", 14))
version_select_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
version_scroll_container = customtkinter.CTkFrame(master=user_version_frame, height=150, fg_color="transparent")
version_scroll_container.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
version_scroll_container.grid_propagate(0)
version_variable = customtkinter.StringVar()
version_scroll_frame = customtkinter.CTkScrollableFrame(master=version_scroll_container, fg_color="transparent")
version_scroll_frame.pack(fill="both", expand=True)
show_snapshots_checkbox = customtkinter.CTkCheckBox(master=user_version_frame, text="Show Snapshots and other versions")
show_snapshots_checkbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
user_version_frame.columnconfigure(1, weight=1)

# Body - Frame 2: (para setear valores de ram y args de java)
java_options_frame = customtkinter.CTkFrame(master=app)
java_options_frame.pack(pady=10, padx=60, fill="x")
ram_label = customtkinter.CTkLabel(master=java_options_frame, text="Custom RAM Allocation: 4096 MB", font=("jetbrains mono", 14))
ram_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
ram_slider = customtkinter.CTkSlider(master=java_options_frame, from_=2048, to=16384, number_of_steps=14, command=lambda value: launcher_logic.update_ram_label(value, ram_label))
ram_slider.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
ram_slider.set(4096)
java_args_label = customtkinter.CTkLabel(master=java_options_frame, text="Custom Java Arguments:", font=("jetbrains mono", 14))
java_entry = customtkinter.CTkEntry(master=java_options_frame, placeholder_text="Optional")
java_args_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
java_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
java_options_frame.columnconfigure(1, weight=1)

# Body - Frame 3 (el manejador de skins)
skin_management_frame = customtkinter.CTkFrame(master=app)
skin_management_frame.pack(pady=10, padx=60, fill="x")
skin_title_label = customtkinter.CTkLabel(master=skin_management_frame, text="Skin manager:", font=("jetbrains mono", 14))
skin_title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
skin_button = customtkinter.CTkButton(master=skin_management_frame, text="Click here to select skin file (.png)")
skin_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
skin_preview_label = customtkinter.CTkLabel(master=skin_management_frame, text="No Preview", width=64, height=64, fg_color="gray20", corner_radius=6)
skin_preview_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")
skin_management_frame.grid_columnconfigure(0, weight=1)

# Cargamos la preview del skin (si hay alguna subida :d)
if last_skin_path and os.path.exists(last_skin_path):
    initial_preview_image = launcher_logic._create_skin_preview_image(last_skin_path, (64, 64))
    if initial_preview_image:
        skin_preview_label.configure(image=initial_preview_image, text="")
        skin_preview_label.image = initial_preview_image

status_label = customtkinter.CTkLabel(master=app, text="Status: Ready to play!", font=("jetbrains mono", 12))

ui_elements = {
    "app": app, "username_entry": username_entry, "version_variable": version_variable,
    "ram_slider": ram_slider, "java_entry": java_entry, "status_label": status_label,
    "skin_preview_label": skin_preview_label, "version_scroll_frame": version_scroll_frame,
    "show_snapshots_checkbox": show_snapshots_checkbox
}

# FOOTER SECTION 

# Creamos su espacio
footer_frame = customtkinter.CTkFrame(master=app)
footer_frame.pack(pady=(10, 10), padx=60, fill="x")

# 2. el boton de play/install
play_button = customtkinter.CTkButton(master=footer_frame, text="Play / Install", width=150, height=40, command=lambda: launcher_logic.launch_or_install_minecraft(ui_elements, ALL_VERSIONS, INSTALLED_IDS))
play_button.pack(pady=20, padx=20)

# 3. conectamos con su configuracion y su posicion
skin_button.configure(command=lambda: launcher_logic.select_and_process_skin(ui_elements))
show_snapshots_checkbox.configure(command=lambda: launcher_logic.update_version_list(ui_elements, ALL_VERSIONS, INSTALLED_IDS))
status_label.pack(pady=(0, 20), padx=10, side="bottom")

# 4. llamamos a la logica para cargar la lista de versiones
launcher_logic.update_version_list(ui_elements, ALL_VERSIONS, INSTALLED_IDS)

# el loop para iniciar app
app.mainloop()
