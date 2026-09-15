import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import customtkinter as ctk
import psycopg2

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppAgenda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agenda 3 Patitos")
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.conn_params = {
            "dbname": "postgres",
            "user": "postgres",
            "password": "michiyyo123",
            "host": "localhost",
            "port": "5432",
        }

        self.usuarios_combo = {}
        self.categorias_combo = {}
        self.categorias_padre_combo = {}

        self.ubicaciones_combo = {}
        self.eventos_combo = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        self.crear_area_principal()
        self.configurar_estilos()

        self.actualizar_todas_las_tablas()

        if DateEntry is None:
            self.after(500, lambda: messagebox.showwarning(
                "Calendario no instalado",
                "Para usar los selectores de fecha instala:\n\npip install tkcalendar"
            ))

    # -------------------- INFRAESTRUCTURA --------------------

    def obtener_conexion(self):
        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO prototipo, public;")
        return conn

    def ejecutar_consulta(self, sql, params=None, fetch=False):
        conn = None
        try:
            conn = self.obtener_conexion()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def crear_treeview(self, parent, columnas, widths):
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tree = ttk.Treeview(contenedor, columns=columnas, show="headings")
        for col, width in zip(columnas, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        return tree

    def seleccionar_modulo(self, nombre):
        self.tabview.set(nombre)
        for modulo, boton in self.botones_nav.items():
            boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=235, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="📅 AGENDA 🦆🦆🦆",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Gestión de usuarios, categorías y eventos",
            font=ctk.CTkFont(size=11),
            wraplength=190,
            justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        self.botones_nav = {}
        for i, (nombre, icono) in enumerate([
            ("Usuarios", "👥"),
            ("Categorías", "📁"),
            ("Eventos", "🗓️"),
        ], start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icono}  {nombre}",
                anchor="w", fg_color="transparent",
                command=lambda n=nombre: self.seleccionar_modulo(n)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[nombre] = btn

        ctk.CTkButton(
            self.sidebar_frame,
            text="🔄  Recargar datos",
            command=self.actualizar_todas_las_tablas
        ).grid(row=5, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="APARIENCIA", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=11, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.option_mode = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.option_mode.set("System")
        self.option_mode.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")

    def crear_area_principal(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, command=self.al_cambiar_pestana)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_categorias = self.tabview.add("Categorías")
        self.tab_eventos = self.tabview.add("Eventos")
        self.tab_ubicaciones = self.tabview.add("Ubicaciones")
        self.tab_disponibilidad = self.tabview.add("Disponibilidad")
        self.tab_tareas = self.tabview.add("Tareas")

        self.configurar_pestana_usuarios()
        self.configurar_pestana_categorias()
        self.configurar_pestana_eventos()

        self.configurar_pestana_ubicaciones()
        self.configurar_pestana_disponibilidad()
        self.configurar_pestana_tareas()

        self.seleccionar_modulo("Usuarios")

    def al_cambiar_pestana(self):
        nombre = self.tabview.get()
        if nombre in self.botones_nav:
            for modulo, boton in self.botones_nav.items():
                boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_encabezado(self, parent, titulo, descripcion):
        ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(parent, text=descripcion, font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=15, pady=(0, 12)
        )

    # -------------------- USUARIOS --------------------

    def configurar_pestana_usuarios(self):
        self.crear_encabezado(self.tab_usuarios, "Usuarios", "Registra, consulta y administra los usuarios de la agenda.")

        cuerpo = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_usuarios = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Apellido", "Registro", "Activo"),
            (70, 160, 160, 160, 80)
        )
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

        ctk.CTkLabel(form, text="Formulario de usuario", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombre.pack(fill="x", padx=10, pady=6)
        self.entry_apellido = ctk.CTkEntry(form, placeholder_text="Apellido")
        self.entry_apellido.pack(fill="x", padx=10, pady=6)

        self.switch_usuario_activo = ctk.CTkSwitch(form, text="Usuario activo")
        self.switch_usuario_activo.select()
        self.switch_usuario_activo.pack(anchor="w", padx=12, pady=10)

        ctk.CTkButton(form, text="➕ Registrar usuario", command=self.agregar_usuario).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_usuario).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_usuario, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_usuario, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def usuario_seleccionado_id(self):
        sel = self.tree_usuarios.selection()
        return self.tree_usuarios.item(sel[0])["values"][0] if sel else None

    def cargar_usuario_seleccionado(self, _=None):
        sel = self.tree_usuarios.selection()
        if not sel:
            return
        vals = self.tree_usuarios.item(sel[0])["values"]
        self.entry_nombre.delete(0, tk.END); self.entry_nombre.insert(0, vals[1])
        self.entry_apellido.delete(0, tk.END); self.entry_apellido.insert(0, vals[2])
        if vals[4]:
            self.switch_usuario_activo.select()
        else:
            self.switch_usuario_activo.deselect()

    def limpiar_form_usuario(self):
        self.tree_usuarios.selection_remove(self.tree_usuarios.selection())
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.switch_usuario_activo.select()

    def agregar_usuario(self):
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("INSERT INTO usuarios (nombre, apellido, activo) VALUES (%s, %s, %s)",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario para actualizar.")
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("UPDATE usuarios SET nombre=%s, apellido=%s, activo=%s WHERE id_usuario=%s",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario actualizado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el usuario seleccionado?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Usuario eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_usuarios(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_usuario, nombre, apellido, fecha_registro, activo FROM usuarios ORDER BY nombre, apellido",
                fetch=True
            )
            for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
            self.usuarios_combo = {}
            for row in rows:
                registro = row[3].strftime("%Y-%m-%d %H:%M") if hasattr(row[3], "strftime") else row[3]
                self.tree_usuarios.insert("", "end", values=(row[0], row[1], row[2], registro, "Sí" if row[4] else "No"))
                etiqueta = f"{row[1]} {row[2]} — #{row[0]}"
                self.usuarios_combo[etiqueta] = row[0]
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    # -------------------- CATEGORÍAS --------------------

    def configurar_pestana_categorias(self):
        self.crear_encabezado(self.tab_categorias, "Categorías", "Organiza los eventos mediante categorías y subcategorías.")

        cuerpo = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=320); form.grid(row=0, column=1, sticky="nsew")

        self.tree_categorias = self.crear_treeview(tabla, ("ID", "Categoría", "Categoría padre"), (80, 230, 230))
        self.tree_categorias.bind("<<TreeviewSelect>>", self.cargar_categoria_seleccionada)

        ctk.CTkLabel(form, text="Formulario de categoría", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_cat_nombre = ctk.CTkEntry(form, placeholder_text="Nombre de la categoría")
        self.entry_cat_nombre.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Categoría padre").pack(anchor="w", padx=10, pady=(10, 2))
        self.combo_cat_padre = ctk.CTkComboBox(form, values=["Sin categoría padre"], state="readonly")
        self.combo_cat_padre.set("Sin categoría padre")
        self.combo_cat_padre.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(form, text="➕ Crear categoría", command=self.agregar_categoria).pack(fill="x", padx=10, pady=(15, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionada", command=self.actualizar_categoria).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nueva / Limpiar", command=self.limpiar_form_categoria, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionada", command=self.eliminar_categoria, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def categoria_seleccionada_id(self):
        sel = self.tree_categorias.selection()
        return self.tree_categorias.item(sel[0])["values"][0] if sel else None

    def cargar_categoria_seleccionada(self, _=None):
        sel = self.tree_categorias.selection()
        if not sel: return
        vals = self.tree_categorias.item(sel[0])["values"]
        self.entry_cat_nombre.delete(0, tk.END); self.entry_cat_nombre.insert(0, vals[1])
        padre = vals[2]
        self.combo_cat_padre.set(padre if padre in self.categorias_padre_combo else "Sin categoría padre")

    def limpiar_form_categoria(self):
        self.tree_categorias.selection_remove(self.tree_categorias.selection())
        self.entry_cat_nombre.delete(0, tk.END); self.combo_cat_padre.set("Sin categoría padre")

    def _padre_id_actual(self):
        valor = self.combo_cat_padre.get()
        return None if valor == "Sin categoría padre" else self.categorias_padre_combo.get(valor)

    def agregar_categoria(self):
        nombre = self.entry_cat_nombre.get().strip()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre de la categoría.")
        try:
            self.ejecutar_consulta("INSERT INTO categorias (nombre, id_categoria_padre) VALUES (%s, %s)",
                                   (nombre, self._padre_id_actual()))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Categoría creada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        nombre = self.entry_cat_nombre.get().strip(); padre = self._padre_id_actual()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre.")
        if padre == cid: return messagebox.showwarning("Relación inválida", "Una categoría no puede ser su propia categoría padre.")
        try:
            self.ejecutar_consulta("UPDATE categorias SET nombre=%s, id_categoria_padre=%s WHERE id_categoria=%s",
                                   (nombre, padre, cid))
            self.actualizar_todas_las_tablas(); messagebox.showinfo("Éxito", "Categoría actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la categoría seleccionada?"): return
        try:
            self.ejecutar_consulta("DELETE FROM categorias WHERE id_categoria=%s", (cid,))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Categoría eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_categorias(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT c.id_categoria, c.nombre, p.nombre
                FROM categorias c
                LEFT JOIN categorias p ON p.id_categoria = c.id_categoria_padre
                ORDER BY c.nombre
            """, fetch=True)
            ids = self.ejecutar_consulta("SELECT id_categoria, nombre FROM categorias ORDER BY nombre", fetch=True)

            for item in self.tree_categorias.get_children(): self.tree_categorias.delete(item)
            self.categorias_combo = {}
            self.categorias_padre_combo = {}
            for cid, nombre in ids:
                etiqueta = f"{nombre} — #{cid}"
                self.categorias_combo[etiqueta] = cid
                self.categorias_padre_combo[etiqueta] = cid
            for row in rows:
                padre = "Sin categoría padre"
                if row[2] is not None:
                    # Buscar etiqueta completa del padre
                    for etiqueta, cid in self.categorias_padre_combo.items():
                        if etiqueta.startswith(f"{row[2]} —"):
                            padre = etiqueta; break
                self.tree_categorias.insert("", "end", values=(row[0], row[1], padre))

            valores_padre = ["Sin categoría padre"] + list(self.categorias_padre_combo.keys())
            self.combo_cat_padre.configure(values=valores_padre)
            if self.combo_cat_padre.get() not in valores_padre:
                self.combo_cat_padre.set("Sin categoría padre")
        except Exception as e:
            print(f"Error cargando categorías: {e}")

    # -------------------- EVENTOS --------------------

    def configurar_pestana_eventos(self):
        self.crear_encabezado(self.tab_eventos, "Eventos", "Programa eventos seleccionando usuarios, categorías, fechas y horas.")

        cuerpo = ctk.CTkFrame(self.tab_eventos, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=350); form.grid(row=0, column=1, sticky="nsew")

        self.tree_eventos = self.crear_treeview(
            tabla, ("ID", "Propietario", "Categoría", "Título", "Inicio", "Fin"),
            (70, 170, 150, 220, 150, 150)
        )
        self.tree_eventos.bind("<<TreeviewSelect>>", self.cargar_evento_seleccionado)

        ctk.CTkLabel(form, text="Formulario de evento", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 12))

        self.entry_ev_titulo = ctk.CTkEntry(form, placeholder_text="Título del evento")
        self.entry_ev_titulo.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Propietario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Categoría").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_categoria = ctk.CTkComboBox(form, values=["Seleccione una categoría"], state="readonly")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_categoria.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Ubicación").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_ubicacion = ctk.CTkComboBox(form, values=["Sin ubicación"], state="readonly")
        self.combo_ev_ubicacion.set("Sin ubicación")
        self.combo_ev_ubicacion.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Inicio").pack(anchor="w", padx=10, pady=(10, 2))
        fila_inicio = ctk.CTkFrame(form, fg_color="transparent"); fila_inicio.pack(fill="x", padx=10)
        self.fecha_inicio = self.crear_selector_fecha(fila_inicio)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)
        self.hora_inicio = ctk.CTkEntry(fila_inicio, placeholder_text="HH:MM", width=75)
        self.hora_inicio.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fin").pack(anchor="w", padx=10, pady=(10, 2))
        fila_fin = ctk.CTkFrame(form, fg_color="transparent"); fila_fin.pack(fill="x", padx=10)
        self.fecha_fin = self.crear_selector_fecha(fila_fin)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        self.hora_fin = ctk.CTkEntry(fila_fin, placeholder_text="HH:MM", width=75)
        self.hora_fin.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_evento).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_evento).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_evento, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_evento, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_evento()

    def crear_selector_fecha(self, parent):
        if DateEntry is not None:
            return DateEntry(parent, date_pattern="yyyy-mm-dd", font=("Arial", 10))
        return ttk.Entry(parent)

    def obtener_fecha(self, widget):
        if DateEntry is not None:
            return widget.get_date().strftime("%Y-%m-%d")
        return widget.get().strip()

    def establecer_fecha(self, widget, valor):
        fecha = valor.date() if hasattr(valor, "date") else datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
        if DateEntry is not None:
            widget.set_date(fecha)
        else:
            widget.delete(0, tk.END); widget.insert(0, fecha.strftime("%Y-%m-%d"))

    def evento_seleccionado_id(self):
        sel = self.tree_eventos.selection()
        return self.tree_eventos.item(sel[0])["values"][0] if sel else None

    def cargar_evento_seleccionado(self, _=None):
        sel = self.tree_eventos.selection()
        if not sel: return
        vals = self.tree_eventos.item(sel[0])["values"]
        self.entry_ev_titulo.delete(0, tk.END); self.entry_ev_titulo.insert(0, vals[3])
        self.combo_ev_usuario.set(vals[1])
        self.combo_ev_categoria.set(vals[2])
        try:
            ini = datetime.strptime(str(vals[4]), "%Y-%m-%d %H:%M")
            fin = datetime.strptime(str(vals[5]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_inicio, ini)
            self.establecer_fecha(self.fecha_fin, fin)
            self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, ini.strftime("%H:%M"))
            self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, fin.strftime("%H:%M"))
        except ValueError:
            pass

    def limpiar_form_evento(self):
        self.tree_eventos.selection_remove(self.tree_eventos.selection())
        self.entry_ev_titulo.delete(0, tk.END)
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_categoria.set("Seleccione una categoría")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_inicio, hoy); self.establecer_fecha(self.fecha_fin, hoy)
        self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, "09:00")
        self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, "10:00")

    def datos_evento_formulario(self):
        titulo = self.entry_ev_titulo.get().strip()
        usuario = self.usuarios_combo.get(self.combo_ev_usuario.get())
        categoria = self.categorias_combo.get(self.combo_ev_categoria.get())
        try:
            inicio = datetime.strptime(f"{self.obtener_fecha(self.fecha_inicio)} {self.hora_inicio.get().strip()}", "%Y-%m-%d %H:%M")
            fin = datetime.strptime(f"{self.obtener_fecha(self.fecha_fin)} {self.hora_fin.get().strip()}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("La hora debe tener formato HH:MM, por ejemplo 09:30.")
        if not titulo or usuario is None or categoria is None:
            raise ValueError("Completa título, propietario y categoría.")
        if fin <= inicio:
            raise ValueError("La fecha y hora de finalización deben ser posteriores al inicio.")
        return usuario, categoria, titulo, inicio, fin

    def agregar_evento(self):
        try:
            datos = self.datos_evento_formulario()
            self.ejecutar_consulta("""
                INSERT INTO eventos
                (id_usuario_propietario, id_categoria, titulo, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s)
            """, datos)
            self.limpiar_form_evento(); self.cargar_datos_eventos()
            messagebox.showinfo("Éxito", "Evento creado correctamente.")
        except Exception as e:
            messagebox.showerror("No se pudo crear el evento", str(e))

    def actualizar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        try:
            usuario, categoria, titulo, inicio, fin = self.datos_evento_formulario()
            self.ejecutar_consulta("""
                UPDATE eventos SET id_usuario_propietario=%s, id_categoria=%s,
                titulo=%s, fecha_inicio=%s, fecha_fin=%s WHERE id_evento=%s
            """, (usuario, categoria, titulo, inicio, fin, eid))
            self.cargar_datos_eventos(); messagebox.showinfo("Éxito", "Evento actualizado.")
        except Exception as e:
            messagebox.showerror("No se pudo actualizar", str(e))

    def eliminar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el evento seleccionado?"): return
        try:
            self.ejecutar_consulta("DELETE FROM eventos WHERE id_evento=%s", (eid,))
            self.limpiar_form_evento(); self.cargar_datos_eventos()
            messagebox.showinfo("Eliminado", "Evento eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_eventos(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT e.id_evento, u.id_usuario, u.nombre, u.apellido,
                       c.id_categoria, c.nombre, e.titulo, e.fecha_inicio, e.fecha_fin
                FROM eventos e
                JOIN usuarios u ON u.id_usuario = e.id_usuario_propietario
                JOIN categorias c ON c.id_categoria = e.id_categoria
                ORDER BY e.fecha_inicio DESC
            """, fetch=True)
            for item in self.tree_eventos.get_children(): self.tree_eventos.delete(item)
            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                categoria = f"{row[5]} — #{row[4]}"
                inicio = row[7].strftime("%Y-%m-%d %H:%M") if hasattr(row[7], "strftime") else row[7]
                fin = row[8].strftime("%Y-%m-%d %H:%M") if hasattr(row[8], "strftime") else row[8]
                self.tree_eventos.insert("", "end", values=(row[0], usuario, categoria, row[6], inicio, fin))

            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            valores_c = ["Seleccione una categoría"] + list(self.categorias_combo.keys())
            self.combo_ev_usuario.configure(values=valores_u)
            self.combo_ev_categoria.configure(values=valores_c)

            self.ubicaciones_combo = {}
            ubi_rows = self.ejecutar_consulta("SELECT id_ubicacion, nombre FROM prototipo.ubicaciones ORDER BY nombre", fetch=True)
            for row in ubi_rows:
                etiqueta = f"{row[1]} - #{row[0]}"
                self.ubicaciones_combo[etiqueta] = row[0]
            valores_ubi = ["Sin ubicación"] + list(self.ubicaciones_combo.keys())
            self.combo_ev_ubicacion.configure(values=valores_ubi)

        except Exception as e:
            print(f"Error cargando eventos: {e}")


# -------------------- UBICACIONES --------------------

    def configurar_pestana_ubicaciones(self):
        ctk.CTkLabel(self.tab_ubicaciones, text="Ubicaciones").pack(pady=5)
        
        self.tree_ubicaciones = ttk.Treeview(
            self.tab_ubicaciones,
            columns=("ID", "Nombre", "Direccion", "Ciudad", "Capacidad"),
            show="headings",
            height=8
        )
        for col in ("ID", "Nombre", "Direccion", "Ciudad", "Capacidad"):
            self.tree_ubicaciones.heading(col, text=col)
            self.tree_ubicaciones.column(col, width=120, anchor="center")
        self.tree_ubicaciones.pack(fill="x", padx=10, pady=5)
        self.tree_ubicaciones.bind("<<TreeviewSelect>>", self.cargar_ubicacion_seleccionada)

        self.entry_ubi_nombre = ctk.CTkEntry(self.tab_ubicaciones, placeholder_text="Nombre")
        self.entry_ubi_nombre.pack(padx=10, pady=2, fill="x")
        
        self.entry_ubi_direccion = ctk.CTkEntry(self.tab_ubicaciones, placeholder_text="Dirección")
        self.entry_ubi_direccion.pack(padx=10, pady=2, fill="x")
        
        self.entry_ubi_ciudad = ctk.CTkEntry(self.tab_ubicaciones, placeholder_text="Ciudad")
        self.entry_ubi_ciudad.pack(padx=10, pady=2, fill="x")
        
        self.entry_ubi_capacidad = ctk.CTkEntry(self.tab_ubicaciones, placeholder_text="Capacidad")
        self.entry_ubi_capacidad.pack(padx=10, pady=2, fill="x")
        
        ctk.CTkButton(self.tab_ubicaciones, text="Crear", command=self.agregar_ubicacion).pack(pady=5)
        ctk.CTkButton(self.tab_ubicaciones, text="Actualizar", command=self.actualizar_ubicacion).pack(pady=5)
        ctk.CTkButton(self.tab_ubicaciones, text="Eliminar", command=self.eliminar_ubicacion).pack(pady=5)
        ctk.CTkButton(self.tab_ubicaciones, text="Ver ranking", command=self.ver_ranking_ubicaciones).pack(pady=5)

    def cargar_datos_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_ubicacion, nombre, direccion, ciudad, capacidad "
                "FROM prototipo.ubicaciones ORDER BY nombre",
                fetch=True
            )
            for item in self.tree_ubicaciones.get_children():
                self.tree_ubicaciones.delete(item)
            for row in rows:
                self.tree_ubicaciones.insert("", "end", values=row)
        except Exception as e:
            print("Error cargando ubicaciones:", e)


    def limpiar_form_ubicacion(self):                   
        self.tree_ubicaciones.selection_remove(self.tree_ubicaciones.selection())
        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_capacidad.delete(0, tk.END)

    def cargar_ubicacion_seleccionada(self, _=None):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return
        vals = self.tree_ubicaciones.item(sel[0])["values"]
        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_nombre.insert(0, vals[1])
        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_direccion.insert(0, vals[2])
        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_ciudad.insert(0, vals[3])
        self.entry_ubi_capacidad.delete(0, tk.END)
        self.entry_ubi_capacidad.insert(0, vals[4])

    def agregar_ubicacion(self):
        nombre = self.entry_ubi_nombre.get().strip()
        direccion = self.entry_ubi_direccion.get().strip()
        ciudad = self.entry_ubi_ciudad.get().strip()
        capacidad = self.entry_ubi_capacidad.get().strip()
        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "INSERT INTO prototipo.ubicaciones (nombre, direccion, ciudad, capacidad) VALUES (%s, %s, %s, %s)",
                (nombre, direccion, ciudad, capacidad)
            )
            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicación registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))


    def actualizar_ubicacion(self):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una ubicación.")
        uid = self.tree_ubicaciones.item(sel[0])["values"][0]
        nombre = self.entry_ubi_nombre.get().strip()
        direccion = self.entry_ubi_direccion.get().strip()
        ciudad = self.entry_ubi_ciudad.get().strip()
        capacidad = self.entry_ubi_capacidad.get().strip()
        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "UPDATE prototipo.ubicaciones SET nombre=%s, direccion=%s, ciudad=%s, capacidad=%s WHERE id_ubicacion=%s",
                (nombre, direccion, ciudad, capacidad, uid)
            )
            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicación actualizada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))


    def eliminar_ubicacion(self):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una ubicación.")
        uid = self.tree_ubicaciones.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar la ubicación seleccionada?"):
            return
        try:
            self.ejecutar_consulta(
                "DELETE FROM prototipo.ubicaciones WHERE id_ubicacion=%s",
                (uid,)
            )
            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicación eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))


    def ver_ranking_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT nombre, ciudad, total_eventos FROM prototipo.vw_ranking_ubicaciones",
                fetch=True
            )
        except Exception as e:
            return messagebox.showerror("Error de base de datos", str(e))
        texto = "Ranking de ubicaciones:\n\n"
        for r in rows:
            texto += f"{r[0]} ({r[1]}) - {r[2]} eventos\n"
        if not rows:
            texto = "No hay ubicaciones registradas."
        messagebox.showinfo("Ranking", texto)


# -------------------- DISPONIBILIDAD --------------------


    def configurar_pestana_disponibilidad(self):
        self.crear_encabezado(self.tab_disponibilidad, "Disponibilidad", "Administra las franjas de disponibilidad de los usuarios.")
        
        cuerpo = ctk.CTkFrame(self.tab_disponibilidad, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        
        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=350); form.grid(row=0, column=1, sticky="nsew")
        
        self.tree_disponibilidad = self.crear_treeview(
            tabla, ("ID", "Usuario", "Fecha", "Inicio", "Fin", "Tipo"), 
            (60, 160, 100, 90, 90, 110)
        )
        self.tree_disponibilidad.bind("<<TreeviewSelect>>", self.cargar_disponibilidad_seleccionada)
          
        ctk.CTkLabel(form, text="Formulario de disponibilidad", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 12))
        
        ctk.CTkLabel(form, text="Usuario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_disp_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_disp_usuario.set("Seleccione un usuario")
        self.combo_disp_usuario.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(form, text="Fecha").pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_disp_fecha = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        self.entry_disp_fecha.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(form, text="Hora inicio").pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_disp_inicio = ctk.CTkEntry(form, placeholder_text="HH:MM")
        self.entry_disp_inicio.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(form, text="Hora fin").pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_disp_fin = ctk.CTkEntry(form, placeholder_text="HH:MM")
        self.entry_disp_fin.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(form, text="Tipo").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_disp_tipo = ctk.CTkComboBox(form, values=["Disponible", "Ocupado", "No disponible"], state="readonly")
        self.combo_disp_tipo.set("Disponible")
        self.combo_disp_tipo.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(form, text="+ Crear disponibilidad", command=self.agregar_disponibilidad).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="Nuevo / Limpiar", command=self.limpiar_form_disponibilidad, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="+ Actualizar seleccionada", command=self.actualizar_disponibilidad).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="Eliminar seleccionada", command=self.eliminar_disponibilidad, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)


    def cargar_datos_disponibilidad(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT d.id_disponibilidad, u.nombre || ' ' || u.apellido, 
                    d.fecha, d.hora_inicio, d.hora_fin, td.nombre
                FROM disponibilidades d
                JOIN usuarios u ON u.id_usuario = d.id_usuario
                JOIN tipos_disponibilidad td ON td.id_tipo = d.id_tipo
                ORDER BY d.fecha DESC
            """, fetch=True)
            for item in self.tree_disponibilidad.get_children():
                self.tree_disponibilidad.delete(item)
            for row in rows:
                self.tree_disponibilidad.insert("", "end", values=row)
            
            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            self.combo_disp_usuario.configure(values=valores_u)
        except Exception as e:
            print("Error cargando disponibilidad:", e)


    def agregar_disponibilidad(self):
        usuario = self.usuarios_combo.get(self.combo_disp_usuario.get())
        fecha = self.entry_disp_fecha.get().strip()
        inicio = self.entry_disp_inicio.get().strip()
        fin = self.entry_disp_fin.get().strip()
        tipos = {"Disponible": 1, "Ocupado": 2, "No disponible": 3}
        tipo = tipos[self.combo_disp_tipo.get()]
        if usuario is None or not fecha or not inicio or not fin:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "INSERT INTO prototipo.disponibilidades (id_usuario, fecha, hora_inicio, hora_fin, id_tipo) VALUES (%s, %s, %s, %s, %s)",
                (usuario, fecha, inicio, fin, tipo)
            )
            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Disponibilidad registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def limpiar_form_disponibilidad(self):
        self.tree_disponibilidad.selection_remove(self.tree_disponibilidad.selection())
        self.combo_disp_usuario.set("Seleccione un usuario")
        self.entry_disp_fecha.delete(0, tk.END)
        self.entry_disp_inicio.delete(0, tk.END)
        self.entry_disp_fin.delete(0, tk.END)
        self.combo_disp_tipo.set("Disponible")

    def cargar_disponibilidad_seleccionada(self, _=None):
        sel = self.tree_disponibilidad.selection()
        if not sel:
            return
        vals = self.tree_disponibilidad.item(sel[0])["values"]
        usuario_texto = vals[1]
        for etiqueta, uid in self.usuarios_combo.items():
            if etiqueta.startswith(usuario_texto):
                self.combo_disp_usuario.set(etiqueta)
                break
        self.entry_disp_fecha.delete(0, tk.END)
        self.entry_disp_fecha.insert(0, str(vals[2]))
        self.entry_disp_inicio.delete(0, tk.END)
        self.entry_disp_inicio.insert(0, str(vals[3]))
        self.entry_disp_fin.delete(0, tk.END)
        self.entry_disp_fin.insert(0, str(vals[4]))
        self.combo_disp_tipo.set(vals[5])

    def actualizar_disponibilidad(self):
        sel = self.tree_disponibilidad.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una disponibilidad.")
        did = self.tree_disponibilidad.item(sel[0])["values"][0]
        usuario = self.usuarios_combo.get(self.combo_disp_usuario.get())
        fecha = self.entry_disp_fecha.get().strip()
        inicio = self.entry_disp_inicio.get().strip()
        fin = self.entry_disp_fin.get().strip()
        tipos = {"Disponible": 1, "Ocupado": 2, "No disponible": 3}
        tipo = tipos[self.combo_disp_tipo.get()]
        if usuario is None or not fecha or not inicio or not fin:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "UPDATE prototipo.disponibilidades SET id_usuario=%s, fecha=%s, hora_inicio=%s, hora_fin=%s, id_tipo=%s WHERE id_disponibilidad=%s",
                (usuario, fecha, inicio, fin, tipo, did)
            )
            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Disponibilidad actualizada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def eliminar_disponibilidad(self):
        sel = self.tree_disponibilidad.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una disponibilidad.")
        did = self.tree_disponibilidad.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar la disponibilidad seleccionada?"):
            return
        try:
            self.ejecutar_consulta(
                "DELETE FROM prototipo.disponibilidades WHERE id_disponibilidad=%s",
                (did,)
            )
            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Disponibilidad eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))
  
# -------------------- TAREAS --------------------

    def configurar_pestana_tareas(self):
        self.crear_encabezado(self.tab_tareas, "Tareas", "Gestión de tareas por evento.")
        
        self.tree_tareas = self.crear_treeview(
            self.tab_tareas, 
            ("ID", "Evento", "Título", "Prioridad", "Responsable", "Estado", "Fecha límite"),
            (50, 160, 180, 90, 150, 100, 110)
        )

        self.tree_tareas.bind("<<TreeviewSelect>>", self.cargar_tarea_seleccionada)
        
        self.entry_tar_titulo = ctk.CTkEntry(self.tab_tareas, placeholder_text="Título de la tarea")
        self.entry_tar_titulo.pack(padx=10, pady=4, fill="x")

        ctk.CTkLabel(self.tab_tareas, text="Evento").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tar_evento = ctk.CTkComboBox(self.tab_tareas, values=["Seleccione un evento"], state="readonly")
        self.combo_tar_evento.set("Seleccione un evento")
        self.combo_tar_evento.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkLabel(self.tab_tareas, text="Responsable").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tar_responsable = ctk.CTkComboBox(self.tab_tareas, values=["Seleccione un usuario"], state="readonly")
        self.combo_tar_responsable.set("Seleccione un usuario")
        self.combo_tar_responsable.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkLabel(self.tab_tareas, text="Prioridad").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tar_prioridad = ctk.CTkComboBox(self.tab_tareas, values=["Baja", "Media", "Alta"], state="readonly")
        self.combo_tar_prioridad.set("Media")
        self.combo_tar_prioridad.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkLabel(self.tab_tareas, text="Fecha límite").pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_tar_fecha = ctk.CTkEntry(self.tab_tareas, placeholder_text="YYYY-MM-DD")
        self.entry_tar_fecha.pack(padx=10, pady=4, fill="x")

        ctk.CTkLabel(self.tab_tareas, text="Estado").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tar_estado = ctk.CTkComboBox(self.tab_tareas, values=["Pendiente", "En progreso", "Completada", "Cancelada"], state="readonly")
        self.combo_tar_estado.set("Pendiente")
        self.combo_tar_estado.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkButton(self.tab_tareas, text="Crear", command=self.agregar_tarea).pack(pady=5)
        ctk.CTkButton(self.tab_tareas, text="Limpiar", command=self.limpiar_form_tarea, fg_color="gray").pack(pady=5)
        ctk.CTkButton(self.tab_tareas, text="Actualizar", command=self.actualizar_tarea).pack(pady=5)
        ctk.CTkButton(self.tab_tareas, text="Eliminar", command=self.eliminar_tarea, fg_color="#b33939", hover_color="#8f2d2d").pack(pady=5)
        ctk.CTkButton(self.tab_tareas, text="Ver tareas vencidas", command=self.ver_tareas_vencidas).pack(pady=5)
        ctk.CTkButton(self.tab_tareas, text="Ver carga de trabajo", command=self.ver_carga_trabajo).pack(pady=5)

    def agregar_tarea(self):
        titulo = self.entry_tar_titulo.get().strip()
        evento = self.eventos_combo.get(self.combo_tar_evento.get())
        responsable = self.usuarios_combo.get(self.combo_tar_responsable.get())
        prioridad = self.combo_tar_prioridad.get()
        fecha = self.entry_tar_fecha.get().strip()
        if not titulo or evento is None or responsable is None or not fecha:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "INSERT INTO prototipo.tareas (id_evento, id_usuario_responsable, titulo, prioridad, fecha_limite) VALUES (%s, %s, %s, %s, %s)",
                (evento, responsable, titulo, prioridad, fecha)
            )
            self.entry_tar_titulo.delete(0, tk.END)
            self.entry_tar_fecha.delete(0, tk.END)
            messagebox.showinfo("Éxito", "Tarea creada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def cargar_tarea_seleccionada(self, _=None):
        sel = self.tree_tareas.selection()
        if not sel:
            return
        vals = self.tree_tareas.item(sel[0])["values"]
        self.entry_tar_titulo.delete(0, tk.END)
        self.entry_tar_titulo.insert(0, vals[2])
        self.entry_tar_fecha.delete(0, tk.END)
        self.entry_tar_fecha.insert(0, str(vals[6]))
        self.combo_tar_prioridad.set(vals[3])
        for etiqueta in self.eventos_combo:
            if etiqueta.startswith(str(vals[1])):
                self.combo_tar_evento.set(etiqueta)
                break
        for etiqueta in self.usuarios_combo:
            if etiqueta.startswith(str(vals[4])):
                self.combo_tar_responsable.set(etiqueta)
                break

    def cargar_datos_tareas(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT t.id_tarea, e.titulo, t.titulo, t.prioridad,
                       u.nombre || ' ' || u.apellido, t.estado, t.fecha_limite
                FROM tareas t
                JOIN eventos e ON e.id_evento = t.id_evento
                JOIN usuarios u ON u.id_usuario = t.id_usuario_responsable
                ORDER BY t.fecha_limite ASC
            """, fetch=True)
            for item in self.tree_tareas.get_children():
                self.tree_tareas.delete(item)
            for row in rows:
                self.tree_tareas.insert("", "end", values=row)
            
            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            self.combo_tar_responsable.configure(values=valores_u)
            
            self.eventos_combo = {}
            ev_rows = self.ejecutar_consulta("SELECT id_evento, titulo FROM eventos ORDER BY titulo", fetch=True)
            for row in ev_rows:
                etiqueta = f"{row[1]} - #{row[0]}"
                self.eventos_combo[etiqueta] = row[0]
            valores_e = ["Seleccione un evento"] + list(self.eventos_combo.keys())
            self.combo_tar_evento.configure(values=valores_e)
        except Exception as e:
            print("Error cargando tareas:", e)

    def limpiar_form_tarea(self):
        self.tree_tareas.selection_remove(self.tree_tareas.selection())
        self.entry_tar_titulo.delete(0, tk.END)
        self.entry_tar_fecha.delete(0, tk.END)
        self.combo_tar_evento.set("Seleccione un evento")
        self.combo_tar_responsable.set("Seleccione un usuario")
        self.combo_tar_prioridad.set("Media")
        self.combo_tar_estado.set("Pendiente")

    def actualizar_tarea(self):
        sel = self.tree_tareas.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una tarea.")
        tid = self.tree_tareas.item(sel[0])["values"][0]
        titulo = self.entry_tar_titulo.get().strip()
        evento = self.eventos_combo.get(self.combo_tar_evento.get())
        responsable = self.usuarios_combo.get(self.combo_tar_responsable.get())
        prioridad = self.combo_tar_prioridad.get()
        fecha = self.entry_tar_fecha.get().strip()
        estado = self.combo_tar_estado.get()
        if not titulo or evento is None or responsable is None or not fecha:
            return messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
        try:
            self.ejecutar_consulta(
                "UPDATE prototipo.tareas SET id_evento=%s, id_usuario_responsable=%s, titulo=%s, prioridad=%s, fecha_limite=%s, estado=%s WHERE id_tarea=%s",
                (evento, responsable, titulo, prioridad, fecha, estado, tid)
            )
            self.limpiar_form_tarea()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Tarea actualizada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def eliminar_tarea(self):
        sel = self.tree_tareas.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Selecciona una tarea.")
        tid = self.tree_tareas.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar la tarea seleccionada?"):
            return
        try:
            self.ejecutar_consulta(
                "DELETE FROM prototipo.tareas WHERE id_tarea=%s",
                (tid,)
            )
            self.limpiar_form_tarea()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Tarea eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def ver_tareas_vencidas(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT tarea, evento, responsable, fecha_limite, dias_vencida FROM prototipo.vw_tareas_vencidas",
                fetch=True
            )
        except Exception as e:
            return messagebox.showerror("Error de base de datos", str(e))
        texto = "Tareas vencidas:\n\n"
        for r in rows:
            texto += f"{r[0]} ({r[1]}) - {r[2]} - Vencida hace {r[4]} días\n"
        if not rows:
            texto = "No hay tareas vencidas."
        messagebox.showinfo("Tareas vencidas", texto)

    def ver_carga_trabajo(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT usuario, total_pendientes, vencidas FROM prototipo.vw_carga_trabajo",
                fetch=True
            )
        except Exception as e:
            return messagebox.showerror("Error de base de datos", str(e))
        texto = "Carga de trabajo por usuario:\n\n"
        for r in rows:
            texto += f"{r[0]}: {r[1]} pendientes, {r[2]} vencidas\n"
        if not rows:
            texto = "No hay usuarios registrados."
        messagebox.showinfo("Carga de trabajo", texto)
    

    # -------------------- REFRESCO GENERAL --------------------

    def actualizar_todas_las_tablas(self):
        self.cargar_datos_usuarios()
        self.cargar_datos_categorias()
        self.cargar_datos_eventos()

        self.cargar_datos_ubicaciones()
        self.cargar_datos_disponibilidad()
        self.cargar_datos_tareas()

if __name__ == "__main__":
    app = AppAgenda()
    app.mainloop()
