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
#  configuracion default para el UI
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

app = customtkinter.CTk()
app.geometry("600x885")
app.title("MRC Launcher")
app.resizable(False, False)

# Para cargar el icono del launcher
try:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, "assets/logo.ico")
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)
    else:
        print(f"Advertencia: No se encontró el archivo del ícono en: {icon_path}")
except Exception as e:
    print(f"No se pudo cargar el ícono: {e}")

# cargar y guardar datos iniciales y configuración
display_versions = launcher_logic.load_initial_data()
config = launcher_logic.cargar_configuracion()
last_username = config.get("last_username", "")
last_skin_path = config.get("last_skin_path", "")

# todo el UI

# HEADER
header = customtkinter.CTkFrame(master=app)
header.pack(pady=10, padx=60, fill="x")
label = customtkinter.CTkLabel(master=header, text="MRC Launcher", font=("monocraft", 24))
label.pack(pady=12, padx=10)

# BODY
title_body01 = customtkinter.CTkLabel(master=app, text="Setup Options:", font=("jetbrains mono", 16))
title_body01.pack(pady=0, padx=10)

# Frame 1: Usuario y Versión (con el truco del contenedor)
frame01 = customtkinter.CTkFrame(master=app)
frame01.pack(pady=10, padx=60, fill="x")

label_body01 = customtkinter.CTkLabel(master=frame01, text="Minecraft Username:", font=("jetbrains mono", 14))
username_entry = customtkinter.CTkEntry(master=frame01, width=300)
username_entry.insert(0, last_username)
label_body01.grid(row=0, column=0, padx=10, pady=20, sticky="w")

username_entry.grid(row=0, column=1, padx=10, pady=20, sticky="ew")
label_body02 = customtkinter.CTkLabel(master=frame01, text="Select Minecraft Version:", font=("jetbrains mono", 14))
label_body02.grid(row=1, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")

# contenedor para forzar el tamaño
scroll_container = customtkinter.CTkFrame(master=frame01, height=150, fg_color="transparent")
scroll_container.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
scroll_container.grid_propagate(0)

# frame con scroll
version_variable = customtkinter.StringVar(value=display_versions[0] if display_versions else "")
version_scroll_frame = customtkinter.CTkScrollableFrame(master=scroll_container, fg_color="transparent")
version_scroll_frame.pack(fill="both", expand=True)

for version in display_versions:
    radio_button = customtkinter.CTkRadioButton(master=version_scroll_frame, text=version, variable=version_variable, value=version)
    radio_button.pack(fill="x", padx=10, pady=5)

mostrar_snapshots = customtkinter.CTkCheckBox(master=frame01, text="Show Snapshots and other versions")
mostrar_snapshots.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

frame01.columnconfigure(1, weight=1)

# Frame 2: ram y Argumentos de Java
frame02 = customtkinter.CTkFrame(master=app)
frame02.pack(pady=10, padx=60, fill="x")

label_ram = customtkinter.CTkLabel(master=frame02, text="Custom RAM Allocation: 4096 MB", font=("jetbrains mono", 14))
label_ram.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")

slider_ram = customtkinter.CTkSlider(master=frame02, from_=2048, to=16384, number_of_steps=14, command=lambda value: launcher_logic.actualizar_label_ram(value, label_ram))
slider_ram.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
slider_ram.set(4096)

label_body04 = customtkinter.CTkLabel(master=frame02, text="Custom Java Arguments:", font=("jetbrains mono", 14))
java_entry = customtkinter.CTkEntry(master=frame02, placeholder_text="Opcional")
label_body04.grid(row=2, column=0, padx=10, pady=10, sticky="w")
java_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

frame02.columnconfigure(1, weight=1)

# Frame 3: Gestion de la Skin
frame03 = customtkinter.CTkFrame(master=app)
frame03.pack(pady=10, padx=60, fill="x")

title_skin = customtkinter.CTkLabel(master=frame03, text="Skin manager:", font=("jetbrains mono", 14))
title_skin.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

skin_button = customtkinter.CTkButton(master=frame03, text="Click here to select skin file (.png)")
skin_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

skin_preview_label = customtkinter.CTkLabel(master=frame03, text="Sin Preview", width=64, height=64, fg_color="gray20", corner_radius=6)
skin_preview_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")

frame03.grid_columnconfigure(0, weight=1)

if last_skin_path and os.path.exists(last_skin_path):
    initial_preview_image = launcher_logic._create_skin_preview_image(last_skin_path, (64, 64))
    if initial_preview_image:
        skin_preview_label.configure(image=initial_preview_image, text="")
        skin_preview_label.image = initial_preview_image

status_label = customtkinter.CTkLabel(master=app, text="Status: Ready to play!", font=("jetbrains mono", 12))

ui_elements = {
    "app": app,
    "username_entry": username_entry,
    "version_variable": version_variable,
    "slider_ram": slider_ram,
    "java_entry": java_entry,
    "status_label": status_label,
    "skin_preview_label": skin_preview_label,
    "version_scroll_frame": version_scroll_frame,
    "show_snapshots_checkbox": mostrar_snapshots,
}

skin_button.configure(command=lambda: launcher_logic.seleccionar_y_procesar_skin(ui_elements))

# FOOTER
footer = customtkinter.CTkFrame(master=app)
footer.pack(pady=(10, 10), padx=60, fill="x")
button01 = customtkinter.CTkButton(master=footer, text="Play / Install", width=150, height=40, command=lambda: launcher_logic.lanzar_o_instalar_minecraft(ui_elements))
button01.pack(pady=20, padx=20)

status_label.pack(pady=(0, 20), padx=10, side="bottom")


app.mainloop()

