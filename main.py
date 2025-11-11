import os
import sys
import subprocess
import threading
import queue
import webbrowser
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

import funciones

# Constantes de la UI
COLOR_ACENTO = "#4caf50"
COLOR_ACENTO_HOVER = "#45a049"
COLOR_FONDO_PRINCIPAL = "#3b3b3b"

PADDING_EXTERIOR = 20
PADDING_SECCION = 8
PADDING_WIDGET_X = 10
PADDING_WIDGET_Y = 10
PADDING_INTERNO = 5

FUENTE_UI = ("Jetbrains Mono", 14)
FUENTE_TITULO = ("Monocraft", 20)
FUENTE_ESTADO = ("Monocraft", 16)
FUENTE_BOTON_LANZAR = ("Monocraft", 20)
FUENTE_ENCABEZADO = ("Monocraft", 16)

# Funcion de ayuda para la UI, el menu de ajustes pues
def _create_skin_preview_image(path, size):
    """Crea un objeto CTkImage para la vista previa de la skin."""
    try:
        return ctk.CTkImage(
            light_image=Image.open(path),
            dark_image=Image.open(path),
            size=size,
        )
    except Exception as e:
        print(f"Error al crear imagen de preview: {e}")
        return None

class PaginaAjustes(ctk.CTkToplevel):
    """Una ventana para gestionar todos los ajustes del launcher."""
    def __init__(self, master, ruta_icono=None):
        super().__init__(master)
        self.transient(master)
        self.title("Settings")
        self.geometry("750x550")
        self.resizable(False, False)

        self.ruta_icono = ruta_icono

        if self.ruta_icono and os.path.exists(self.ruta_icono):
            try:
                self.after(250, lambda: self.iconbitmap(self.ruta_icono))
            except Exception as e:
                print(f"No se pudo establecer el ícono de la ventana de ajustes: {e}")

        self.master_app = master

        self._crear_widgets()
        self._poblar_datos_guardados()

    def _crear_widgets(self):
        ctk.CTkLabel(self, text="Launcher Settings", font=FUENTE_ENCABEZADO).pack(pady=PADDING_WIDGET_Y)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PADDING_EXTERIOR, pady=PADDING_INTERNO)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # Columna izquierda (skin Manager)
        left_column = ctk.CTkFrame(main_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_SECCION))

        ctk.CTkLabel(left_column, text="Skin Manager", font=FUENTE_ENCABEZADO).pack(pady=(PADDING_WIDGET_Y, PADDING_INTERNO))

        self.etiqueta_vista_previa_skin = ctk.CTkLabel(
            left_column,
            text="No skin",
            width=200,
            height=200,
            fg_color="gray20",
            corner_radius=10,
        )

        self.etiqueta_vista_previa_skin.pack(pady=PADDING_WIDGET_Y, padx=PADDING_WIDGET_X, expand=True)

        self.boton_skin = ctk.CTkButton(
            left_column,
            text="Select Skin",
            command=self._handle_skin_selection,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        )

        self.boton_skin.pack(pady=PADDING_WIDGET_Y, padx=PADDING_WIDGET_X, fill="x")

        # Columna derecha (ajustes)
        right_column = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(PADDING_SECCION, 0))

        ram_jvm_frame = ctk.CTkFrame(right_column)
        ram_jvm_frame.pack(fill="x", pady=(0, PADDING_SECCION))

        ctk.CTkLabel(
            ram_jvm_frame,
            text="Memory & JVM Options",
            font=FUENTE_ENCABEZADO,
            anchor="w",
        ).pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, 0))

        self.etiqueta_ram = ctk.CTkLabel(
            ram_jvm_frame,
            text="RAM Allocation: 512 MB",
            font=FUENTE_UI,
            anchor="w",
        )

        self.etiqueta_ram.pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, 0))

        self.deslizador_ram = ctk.CTkSlider(
            ram_jvm_frame,
            from_=1024,
            to=12288,
            number_of_steps=22,
            command=self._actualizar_etiqueta_ram,
            button_color=COLOR_ACENTO,
        )

        self.deslizador_ram.pack(fill="x", padx=PADDING_WIDGET_X, pady=PADDING_WIDGET_Y)

        self.campo_java = ctk.CTkEntry(
            ram_jvm_frame,
            placeholder_text="e.g., -XX:+UseG1GC",
            font=FUENTE_UI,
        )

        self.campo_java.pack(fill="x", padx=PADDING_WIDGET_X, pady=(0, PADDING_WIDGET_Y))
        
        api_frame = ctk.CTkFrame(right_column)
        api_frame.pack(fill="x", pady=PADDING_SECCION)

        ctk.CTkLabel(
            api_frame,
            text="AI Settings (Google Gemini)",
            font=FUENTE_ENCABEZADO,
            anchor="w",
        ).pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, 0))

        self.campo_api_key = ctk.CTkEntry(
            api_frame,
            placeholder_text="Enter your Google Gemini API Key",
            font=FUENTE_UI,
            show="*",
        )

        self.campo_api_key.pack(fill="x", padx=PADDING_WIDGET_X, pady=(0, PADDING_WIDGET_Y))
        
        dir_frame = ctk.CTkFrame(right_column)
        dir_frame.pack(fill="x", pady=(PADDING_SECCION, 0))

        ctk.CTkLabel(
            dir_frame,
            text="Minecraft Directory:",
            font=FUENTE_UI,
            anchor="w",
        ).pack(fill="x", padx=PADDING_WIDGET_X)

        dir_entry = ctk.CTkEntry(dir_frame, font=FUENTE_UI)
        dir_entry.insert(0, funciones.MINECRAFT_DIRECTORY)
        dir_entry.configure(state="disabled")
        dir_entry.pack(fill="x", padx=PADDING_WIDGET_X, pady=PADDING_INTERNO)

        delete_button = ctk.CTkButton(
            right_column,
            text="Delete All Stored Data",
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self._solicitar_confirmacion_borrado,
        )

        delete_button.pack(fill="x", pady=(PADDING_SECCION * 2, 0), ipady=PADDING_INTERNO)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=PADDING_EXTERIOR, pady=PADDING_WIDGET_Y)

        btn_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Save & Close",
            command=self._guardar_y_cerrar,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        ).grid(row=0, column=0, padx=PADDING_INTERNO, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        ).grid(row=0, column=1, padx=PADDING_INTERNO, sticky="ew")

    def _poblar_datos_guardados(self):
        self.deslizador_ram.set(self.master_app.ram_guardada)

        self.etiqueta_ram.configure(text=f"RAM Allocation: {self.master_app.ram_guardada} MB")

        if self.master_app.jvm_args_guardados:
            self.campo_java.insert(0, self.master_app.jvm_args_guardados)

        if self.master_app.api_key_guardada:
            self.campo_api_key.insert(0, self.master_app.api_key_guardada)

        if self.master_app.ultima_ruta_skin and os.path.exists(self.master_app.ultima_ruta_skin):
            try:
                imagen_previa = _create_skin_preview_image(self.master_app.ultima_ruta_skin, (200, 200))

                if imagen_previa:
                    self.etiqueta_vista_previa_skin.configure(image=imagen_previa, text="")
            except Exception as e:
                print(f"No se pudo cargar la vista previa de la skin en ajustes: {e}")

    def _handle_skin_selection(self):
        version_id = self.master_app.elementos_ui["version_variable"].get()
        if not version_id:
            self.master_app._establecer_estado("Please select a Minecraft version first!", "orange")
            return
        skin_path = filedialog.askopenfilename(title="Select your skin", filetypes=[("PNG Files", "*.png")])

        if not skin_path:
            return

        success, message = funciones.process_skin(skin_path, version_id)
        color = "green" if success else "red"

        self.master_app._establecer_estado(message, color)

        if success:
            new_preview = _create_skin_preview_image(skin_path, (200, 200))

            if new_preview:
                self.etiqueta_vista_previa_skin.configure(image=new_preview, text="")

            config = self.master_app.config
            config["last_skin_path"] = skin_path
            funciones.save_configuration(config)
            self.master_app.ultima_ruta_skin = skin_path

    def _solicitar_confirmacion_borrado(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Deletion")
        dialog.geometry("400x180")

        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        if self.ruta_icono and os.path.exists(self.ruta_icono):
            dialog.after(250, lambda: dialog.iconbitmap(self.ruta_icono))

        ctk.CTkLabel(
            dialog,
            text=(
                "Are you sure you want to delete all saved data?\n"
                "(Username, settings, API key, skin...)\n\n"
                "This action cannot be undone."
            ),
            font=FUENTE_UI,
        ).pack(pady=20, padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        btn_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        ).grid(row=0, column=0, padx=PADDING_INTERNO, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Yes, Delete",
            command=lambda: self._ejecutar_borrado(dialog),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
        ).grid(row=0, column=1, padx=PADDING_INTERNO, sticky="ew")

    def _ejecutar_borrado(self, dialog_to_close):
        dialog_to_close.destroy()

        funciones.delete_all_user_data()

        final_dialog = ctk.CTkToplevel(self.master_app)
        final_dialog.title("Data Deleted")
        final_dialog.geometry("350x150")

        final_dialog.transient(self.master_app)
        final_dialog.grab_set()
        final_dialog.resizable(False, False)

        if self.ruta_icono and os.path.exists(self.ruta_icono):
            final_dialog.after(250, lambda: final_dialog.iconbitmap(self.ruta_icono))

        ctk.CTkLabel(
            final_dialog,
            text="All stored data has been deleted.\nThe application will now close.",
            font=FUENTE_UI,
        ).pack(pady=20, padx=20)

        ctk.CTkButton(
            final_dialog,
            text="OK",
            command=self.master_app.destroy,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        ).pack(pady=10, padx=20)

    def _actualizar_etiqueta_ram(self, value):
        self.etiqueta_ram.configure(text=f"RAM Allocation: {int(value)} MB")

    def _guardar_y_cerrar(self):
        config = self.master_app.config

        config["ram_mb"] = int(self.deslizador_ram.get())
        config["jvm_args"] = self.campo_java.get()
        config["google_api_key"] = self.campo_api_key.get().strip()

        funciones.save_configuration(config)

        self.master_app.ram_guardada = config["ram_mb"]
        self.master_app.jvm_args_guardados = config["jvm_args"]
        self.master_app.api_key_guardada = config["google_api_key"]

        self.master_app._establecer_estado("Settings saved successfully!", "green")

        self.destroy()

class LanzadorMcl(ctk.CTk):
    """Clase principal para la aplicación MCL Launcher (Modo Offline)."""
    def __init__(self):
        super().__init__()

        self.estado_job_id = None
        self.ventana_ajustes = None

        self.ruta_icono = None
        self.cola_ia = queue.Queue()

        self._configurar_ventana()
        self._cargar_datos()
        self._crear_widgets()
        self._poblar_datos_iniciales()
        self._vincular_eventos()
        self._procesar_cola_ia()

    def _configurar_ventana(self):
        self.geometry("1100x700")
        self.resizable(False, False)
        self.title("MCL Launcher")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        try:
            base_path = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))

            self.ruta_icono = os.path.join(base_path, "assets", "logo.ico")

            if os.path.exists(self.ruta_icono):
                self.after(250, lambda: self.iconbitmap(self.ruta_icono))
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")

    def _cargar_datos(self):
        self.config = funciones.load_configuration()

        self.TODAS_LAS_VERSIONES, self.IDS_INSTALADAS = funciones.load_initial_data()

        self.ultimo_usuario = self.config.get("last_username", "")
        self.ultima_ruta_skin = self.config.get("last_skin_path", "")

        self.ram_guardada = self.config.get("ram_mb", 512)
        self.jvm_args_guardados = self.config.get("jvm_args", "")
        self.api_key_guardada = self.config.get("google_api_key", "")

    def _crear_widgets(self):
        seccion_principal = ctk.CTkFrame(self, fg_color=COLOR_FONDO_PRINCIPAL)
        seccion_principal.pack(
            pady=(PADDING_WIDGET_Y, PADDING_INTERNO),
            padx=PADDING_EXTERIOR,
            fill="both",
            expand=True,
        )

        self.panel_izquierdo = ctk.CTkFrame(seccion_principal, width=400)
        self.panel_izquierdo.pack(
            side="left",
            fill="both",
            expand=False,
            padx=PADDING_SECCION,
            pady=PADDING_SECCION,
        )

        self.panel_derecho = ctk.CTkFrame(seccion_principal)
        self.panel_derecho.pack(
            side="right",
            fill="both",
            expand=True,
            padx=PADDING_SECCION,
            pady=PADDING_SECCION,
        )

        self.panel_inferior = ctk.CTkFrame(self, fg_color=COLOR_FONDO_PRINCIPAL, height=100)
        self.panel_inferior.pack(
            side="bottom",
            fill="x",
            padx=PADDING_EXTERIOR,
            pady=(PADDING_INTERNO, PADDING_WIDGET_Y),
        )

        self.elementos_ui = {"version_variable": ctk.StringVar(master=self), "app": self}

        self._crear_panel_izquierdo()
        self._crear_panel_derecho()
        self._crear_panel_inferior()

    def _crear_panel_izquierdo(self):
        marco_usuario = ctk.CTkFrame(self.panel_izquierdo)
        marco_usuario.pack(fill="x", padx=PADDING_SECCION, pady=PADDING_SECCION)

        ctk.CTkLabel(
            marco_usuario,
            text="Minecraft Username:",
            font=FUENTE_UI,
            anchor="w",
        ).pack(anchor="w", fill="x", pady=(PADDING_WIDGET_Y, 0), padx=PADDING_WIDGET_X)

        self.campo_usuario = ctk.CTkEntry(
            marco_usuario,
            font=FUENTE_UI,
            placeholder_text="Enter your username",
        )

        self.campo_usuario.pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, PADDING_SECCION))
        self.elementos_ui["username_entry"] = self.campo_usuario

        marco_version = ctk.CTkFrame(self.panel_izquierdo)
        marco_version.pack(fill="both", expand=True, padx=PADDING_SECCION, pady=PADDING_SECCION)

        marco_version.columnconfigure(0, weight=1)
        marco_version.rowconfigure(1, weight=1)

        ctk.CTkLabel(
            marco_version,
            text="Select Minecraft Version:",
            font=FUENTE_UI,
        ).grid(row=0, column=0, padx=PADDING_WIDGET_X, pady=(PADDING_WIDGET_Y, 0), sticky="w")

        self.elementos_ui["version_scroll_frame"] = ctk.CTkScrollableFrame(marco_version, fg_color="transparent")
        self.elementos_ui["version_scroll_frame"].grid(
            row=1,
            column=0,
            padx=PADDING_WIDGET_X,
            pady=PADDING_INTERNO,
            sticky="nsew",
        )

        self.checkbox_snapshots = ctk.CTkCheckBox(marco_version, text="Show Snapshots and other versions")
        self.checkbox_snapshots.grid(row=2, column=0, padx=PADDING_WIDGET_X, pady=PADDING_WIDGET_Y, sticky="w")

        self.elementos_ui["show_snapshots_checkbox"] = self.checkbox_snapshots

        marco_info = ctk.CTkFrame(self.panel_izquierdo)
        marco_info.pack(fill="x", expand=False, padx=PADDING_SECCION, pady=PADDING_SECCION)

        self.etiqueta_version_seleccionada = ctk.CTkLabel(marco_info, text="Selected Version: None", font=FUENTE_UI)
        self.etiqueta_version_seleccionada.pack(pady=PADDING_WIDGET_Y, padx=PADDING_WIDGET_X)

        marco_botones = ctk.CTkFrame(marco_info, fg_color="transparent")
        marco_botones.pack(fill="x", padx=PADDING_WIDGET_X, pady=(0, PADDING_WIDGET_Y))

        marco_botones.columnconfigure((0, 1), weight=1)

        estilo = {"fg_color": COLOR_ACENTO, "hover_color": COLOR_ACENTO_HOVER}

        ctk.CTkButton(
            marco_botones,
            text="Open 'versions'",
            command=self._abrir_directorio_versiones,
            **estilo,
        ).grid(row=0, column=0, padx=PADDING_INTERNO, sticky="ew")

        ctk.CTkButton(
            marco_botones,
            text="Open .minecraft",
            command=self._abrir_directorio_minecraft,
            **estilo,
        ).grid(row=0, column=1, padx=PADDING_INTERNO, sticky="ew")

    def _crear_panel_derecho(self):
        ctk.CTkLabel(
            self.panel_derecho,
            text="MCL Launcher - 1.2",
            font=FUENTE_TITULO,
        ).pack(fill="x", padx=PADDING_SECCION, pady=PADDING_SECCION)

        marco_input_ia = ctk.CTkFrame(self.panel_derecho)
        marco_input_ia.pack(fill="x", padx=PADDING_SECCION, pady=PADDING_SECCION)

        ctk.CTkLabel(
            marco_input_ia,
            text="Mod Suggestions (AI Feature)",
            font=FUENTE_ENCABEZADO,
            anchor="w",
        ).pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, 0))

        self.campo_entrada_ia = ctk.CTkEntry(
            marco_input_ia,
            font=FUENTE_UI,
            placeholder_text="e.g., performance mods for 1.20.1",
        )

        self.campo_entrada_ia.pack(fill="x", padx=PADDING_WIDGET_X, pady=PADDING_INTERNO)

        self.boton_ia = ctk.CTkButton(
            marco_input_ia,
            text="Get Suggestions",
            command=self._obtener_sugerencias_ia,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        )

        self.boton_ia.pack(fill="x", padx=PADDING_WIDGET_X, pady=(PADDING_INTERNO, PADDING_WIDGET_Y))

        self.marco_sugerencias_ia = ctk.CTkScrollableFrame(self.panel_derecho, label_text="Suggestions")
        self.marco_sugerencias_ia.pack(fill="both", expand=True, padx=PADDING_SECCION, pady=(0, PADDING_SECCION))

        ctk.CTkLabel(
            self.marco_sugerencias_ia,
            text="AI suggestions will appear here... \n if you dont set up the API key, nothing will happen. \n so set it up!",
            font=FUENTE_UI,
            text_color="gray50",
        ).pack(pady=50)

    def _crear_panel_inferior(self):
        marco_jugar = ctk.CTkFrame(self.panel_inferior)
        marco_jugar.pack(fill="both", expand=True, padx=PADDING_SECCION, pady=PADDING_SECCION)

        self.etiqueta_estado = ctk.CTkLabel(marco_jugar, text="Status: Ready", font=FUENTE_ESTADO)
        self.etiqueta_estado.pack(side="left", padx=PADDING_WIDGET_X)

        self.elementos_ui["status_label"] = self.etiqueta_estado

        self.boton_ajustes = ctk.CTkButton(
            marco_jugar,
            text="Settings",
            height=50,
            font=FUENTE_BOTON_LANZAR,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
            command=self._abrir_pagina_ajustes,
        )

        self.boton_ajustes.pack(side="right", padx=PADDING_INTERNO, pady=(PADDING_WIDGET_Y - PADDING_INTERNO))

        self.boton_jugar = ctk.CTkButton(
            marco_jugar,
            text="Launch Game",
            width=200,
            height=50,
            font=FUENTE_BOTON_LANZAR,
            fg_color=COLOR_ACENTO,
            hover_color=COLOR_ACENTO_HOVER,
        )

        self.boton_jugar.place(relx=0.5, rely=0.5, anchor="center")

    def _poblar_datos_iniciales(self):
        if self.ultimo_usuario: self.campo_usuario.insert(0, self.ultimo_usuario)
        funciones.update_version_list(self.elementos_ui, self.TODAS_LAS_VERSIONES, self.IDS_INSTALADAS)

    def _vincular_eventos(self):
        self.checkbox_snapshots.configure(command=lambda: funciones.update_version_list(self.elementos_ui, self.TODAS_LAS_VERSIONES, self.IDS_INSTALADAS))
        self.boton_jugar.configure(command=lambda: funciones.launch_or_install_minecraft(self.elementos_ui, self.TODAS_LAS_VERSIONES, self.IDS_INSTALADAS))
        funciones.bind_version_change(self.elementos_ui, self.etiqueta_version_seleccionada)

    def _abrir_pagina_ajustes(self):
        if self.ventana_ajustes is None or not self.ventana_ajustes.winfo_exists():
            self.ventana_ajustes = PaginaAjustes(self, self.ruta_icono)
        self.ventana_ajustes.focus()

    def _obtener_sugerencias_ia(self):
        prompt = self.campo_entrada_ia.get()
        if not prompt.strip():
            self._establecer_estado("Please describe the \n mods you want.", "orange"); return
        if not self.api_key_guardada:
            self._establecer_estado("API Key not set. \n Please add it in Settings.", "orange"); return
        
        self._establecer_estado("AI is thinking...", "cyan")
        self.boton_ia.configure(state="disabled")
        for widget in self.marco_sugerencias_ia.winfo_children(): widget.destroy()
        
        threading.Thread(target=funciones.call_ia_api_in_thread, args=(prompt, self.api_key_guardada, self.cola_ia), daemon=True).start()

    def _procesar_cola_ia(self):
        try:
            tipo_mensaje, datos = self.cola_ia.get_nowait()
            if tipo_mensaje == "SUCCESS":
                self._poblar_sugerencias(datos)
                self._establecer_estado("Suggestions loaded!", "green")
            elif tipo_mensaje == "ERROR":
                self._establecer_estado(f"AI Error: {datos}", "red")
                ctk.CTkLabel(self.marco_sugerencias_ia, text=f"An error occurred:\n{datos}", font=FUENTE_UI, text_color="gray50").pack(pady=20)
            self.boton_ia.configure(state="normal")
        except queue.Empty: pass
        finally: self.after(100, self._procesar_cola_ia)

    def _poblar_sugerencias(self, mods_sugeridos):
        if not mods_sugeridos:
            ctk.CTkLabel(self.marco_sugerencias_ia, text="AI didn't find any suggestions.", font=FUENTE_UI, text_color="gray50").pack(pady=20)
            return
            
        for mod in mods_sugeridos:
            card = ctk.CTkFrame(self.marco_sugerencias_ia)
            card.pack(fill="x", padx=PADDING_INTERNO, pady=PADDING_INTERNO)
            
            ctk.CTkLabel(card, text=mod.get("name", "Unnamed Mod"), font=(FUENTE_UI[0], FUENTE_UI[1], "bold"), anchor="w").pack(fill="x", padx=PADDING_INTERNO, pady=(PADDING_INTERNO, 0))
            ctk.CTkLabel(card, text=mod.get("description", "No description."), wraplength=450, justify="left", anchor="w").pack(fill="x", padx=PADDING_INTERNO)
            
            bottom_frame = ctk.CTkFrame(card, fg_color="transparent")
            bottom_frame.pack(fill="x", padx=PADDING_INTERNO, pady=PADDING_INTERNO)
            bottom_frame.columnconfigure(2, weight=1)

            ctk.CTkLabel(bottom_frame, text=f"Loader: {mod.get('loader', 'N/A')}", font=(FUENTE_UI[0], 12), text_color="gray").grid(row=0, column=0, sticky="w", padx=(0, PADDING_WIDGET_X))
            ctk.CTkLabel(bottom_frame, text=f"Version: {mod.get('version', 'N/A')}", font=(FUENTE_UI[0], 12), text_color="gray").grid(row=0, column=1, sticky="w")

            mod_url = mod.get("url")
            button = ctk.CTkButton(bottom_frame, text="Go to Page" if mod_url else "No URL", state="normal" if mod_url else "disabled", fg_color=COLOR_ACENTO if mod_url else "gray50", hover_color=COLOR_ACENTO_HOVER, command=lambda url=mod_url: webbrowser.open(url))
            button.grid(row=0, column=3, sticky="e")

    def _restaurar_estado_defecto(self):
        self.etiqueta_estado.configure(text="Status: Ready", text_color="white")
        self.estado_job_id = None

    def _establecer_estado(self, texto, color="white"):
        if self.estado_job_id: self.after_cancel(self.estado_job_id)
        self.etiqueta_estado.configure(text=f"Status: {texto}", text_color=color)
        if texto != "AI is thinking...":
            self.estado_job_id = self.after(5000, self._restaurar_estado_defecto)

    def _abrir_directorio_versiones(self):
        path = os.path.join(funciones.MINECRAFT_DIRECTORY, "versions")
        success, message = funciones.open_directory(path)
        self._establecer_estado(message, "green" if success else "red")

    def _abrir_directorio_minecraft(self):
        success, message = funciones.open_directory(funciones.MINECRAFT_DIRECTORY)
        self._establecer_estado(message, "green" if success else "red")

if __name__ == "__main__":
    app = LanzadorMcl()
    app.mainloop()
