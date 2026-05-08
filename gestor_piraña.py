import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS (SQLite)
# ==========================================

def conectar_db():
    return sqlite3.connect("futbol_plantel.db")

def inicializar_db():
    """Crea la tabla si no existe y carga los iniciales solo la primera vez."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            posicion TEXT NOT NULL,
            pos_secundaria TEXT NOT NULL,
            valoracion INTEGER NOT NULL,
            amigo TEXT
        )
    ''')
    
    # Verificamos si está vacía para cargar los 30 por defecto
    cursor.execute("SELECT COUNT(*) FROM jugadores")
    if cursor.fetchone()[0] == 0:
        plantel_inicial = [
            ("Tucu", "DEF", "Ninguna", 82, ""), ("Fabi", "DEF", "Ninguna", 81, ""), 
            ("Ale", "MED", "Ninguna", 75, ""), ("Dami", "DEF", "Ninguna", 79, ""), 
            ("Martn", "MED", "Ninguna", 84, ""), ("Cesar", "MED", "Ninguna", 79, ""),
            ("Giorgio", "MED", "Ninguna", 81, ""), ("Santiago", "DEL", "Ninguna", 84, ""), 
            ("Toro", "ARQ", "Ninguna", 80, ""), ("Pipino", "MED", "Ninguna", 81, ""), 
            ("Pablito", "MED", "Ninguna", 81, ""), ("Chapa", "MED", "Ninguna", 80, ""),
            ("Rodri", "DEL", "Ninguna", 79, ""), ("Pasteles", "DEL", "Ninguna", 78, ""), 
            ("Tojo", "DEF", "Ninguna", 77, ""), ("Pitu", "DEF", "Ninguna", 78, ""), 
            ("Gusti", "MED", "Ninguna", 77, ""), ("Lucho", "DEL", "Ninguna", 70, ""),
            ("Chizzo", "DEL", "Ninguna", 60, ""), ("Facu Amorena", "DEL", "Ninguna", 76, ""), 
            ("Edgar", "DEF", "Ninguna", 80, ""), ("Gonza", "DEF", "Ninguna", 79, ""), 
            ("Fer", "MED", "Ninguna", 80, ""), ("Nico", "DEL", "Ninguna", 77, ""),
            ("Brian", "MED", "Ninguna", 76, ""), ("Agustiki", "DEL", "Ninguna", 80, ""), 
            ("David", "MED", "Ninguna", 82, ""), ("Nacho", "DEF", "Ninguna", 81, ""), 
            ("Mario", "MED", "Ninguna", 80, "Cesar"), ("Beto", "ARQ", "Ninguna", 77, "Cesar")
        ]
        # CORRECCIÓN: Agregamos pos_secundaria al INSERT
        cursor.executemany("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (?, ?, ?, ?, ?)", plantel_inicial)
        conn.commit()
    conn.close()

# ==========================================
# 2. FUNCIONES DE GESTIÓN (CRUD con SQL)
# ==========================================

def refrescar_tabla():
    for item in tree.get_children():
        tree.delete(item)
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jugadores ORDER BY nombre COLLATE NOCASE ASC")
    for row in cursor.fetchall():
        # row: 0=id, 1=nombre, 2=posicion, 3=pos_secundaria, 4=valoracion, 5=amigo
        tree.insert("", tk.END, iid=row[0], values=(row[1], row[2], row[3], row[4], row[5]))
    conn.close()

def agregar_jugador():
    nombre = entry_nombre.get().strip()
    posicion = combo_posicion.get()
    pos_secundaria = combo_secundaria.get()
    valoracion = entry_valoracion.get()
    amigo = entry_amigo.get().strip()
    if not nombre or not valoracion: return
    conn = conectar_db(); cursor = conn.cursor()
    cursor.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (?, ?, ?, ?, ?)", 
                   (nombre, posicion, pos_secundaria, valoracion, amigo))
    conn.commit(); conn.close()
    refrescar_tabla(); limpiar_formulario()

def modificar_jugador():
    seleccion = tree.selection()
    if not seleccion: return
    conn = conectar_db(); cursor = conn.cursor()
    cursor.execute("UPDATE jugadores SET nombre=?, posicion=?, pos_secundaria=?, valoracion=?, amigo=? WHERE id=?", 
                   (entry_nombre.get(), combo_posicion.get(), combo_secundaria.get(), entry_valoracion.get(), entry_amigo.get(), seleccion[0]))
    conn.commit(); conn.close()
    refrescar_tabla(); limpiar_formulario()

def eliminar_jugador():
    seleccion = tree.selection()
    if not seleccion: return
    if messagebox.askyesno("Confirmar", "¿Eliminar?"):
        conn = conectar_db(); cursor = conn.cursor()
        for item_id in seleccion: cursor.execute("DELETE FROM jugadores WHERE id=?", (item_id,))
        conn.commit(); conn.close()
        refrescar_tabla()

def limpiar_formulario():
    entry_nombre.delete(0, tk.END)
    combo_posicion.set("MED")
    combo_secundaria.set("Ninguna")
    entry_valoracion.delete(0, tk.END)
    entry_amigo.delete(0, tk.END)

def cargar_formulario(event):
    seleccion = tree.selection()
    if seleccion:
        v = tree.item(seleccion[0])['values']
        limpiar_formulario()
        entry_nombre.insert(0, v[0])
        combo_posicion.set(v[1])
        combo_secundaria.set(v[2])
        entry_valoracion.insert(0, v[3])
        entry_amigo.insert(0, v[4] if str(v[4]) != "None" else "")

# ==========================================
# 3. BALANCEO Y ORDEN TÁCTICO (ALGORITMO ACTUALIZADO)
# ==========================================

def generar_equipos():
    seleccionados = tree.selection()
    if len(seleccionados) != 16:
        messagebox.showwarning("Error", f"Seleccioná 16. Van: {len(seleccionados)}")
        return

    convocados = []
    for item_id in seleccionados:
        v = tree.item(item_id)['values']
        convocados.append({
            "nombre": str(v[0]), 
            "posicion": str(v[1]), 
            "pos_secundaria": str(v[2]),
            "valoracion": int(v[3]), 
            "amigo": str(v[4]) if str(v[4]) != "None" else ""
        })

    # Lógica de Grupos y Amigos
    procesados = set(); grupos = []
    for j in convocados:
        if j["nombre"] in procesados: continue
        g = [j]; procesados.add(j["nombre"])
        if j["amigo"]:
            amigo = next((x for x in convocados if x["nombre"] == j["amigo"] and x["nombre"] not in procesados), None)
            if amigo: g.append(amigo); procesados.add(amigo["nombre"])
        inv = next((x for x in convocados if x["amigo"] == j["nombre"] and x["nombre"] not in procesados), None)
        if inv: g.append(inv); procesados.add(inv["nombre"])
        grupos.append(g)

    eq1, eq2 = [], []
    
    # 3.1 Compensación de Arqueros
    arqs = [j for j in convocados if j["posicion"] == "ARQ"]
    grupos_con_arq = [g for g in grupos if any(x["posicion"] == "ARQ" for x in g)]
    grupos_sin_arq = [g for g in grupos if not any(x["posicion"] == "ARQ" for x in g)]

    if len(arqs) == 1:
        eq1.extend(grupos_con_arq[0])
        if grupos_sin_arq:
            m_def_g = max(grupos_sin_arq, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
            eq2.extend(m_def_g)
            grupos_sin_arq.remove(m_def_g)
        grupos_restantes = grupos_sin_arq
    elif len(arqs) == 2:
        if len(grupos_con_arq) >= 2:
            eq1.extend(grupos_con_arq[0])
            eq2.extend(grupos_con_arq[1])
            grupos_restantes = grupos_sin_arq
        else:
            eq1.extend(grupos_con_arq[0])
            grupos_restantes = grupos_sin_arq
    else:
        grupos_restantes = grupos_sin_arq + grupos_con_arq

    def val_eq(e): return sum(x["valoracion"] for x in e)

    # 3.2 Repartir Bloques de Amigos primero
    grupos_amigos = [g for g in grupos_restantes if len(g) > 1]
    grupos_solos = [g for g in grupos_restantes if len(g) == 1]

    grupos_amigos.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
    for g in grupos_amigos:
        if len(eq1) + len(g) <= 8 and (val_eq(eq1) <= val_eq(eq2) or len(eq2) == 8):
            eq1.extend(g)
        else: eq2.extend(g)

    # 3.3 Repartir Línea por Línea
    solos = [g[0] for g in grupos_solos]
    def_s = [j for j in solos if j["posicion"] == "DEF"]
    med_s = [j for j in solos if j["posicion"] == "MED"]
    del_s = [j for j in solos if j["posicion"] == "DEL"]
    arq_s = [j for j in solos if j["posicion"] == "ARQ"]

    def balancear_linea(lista):
        lista.sort(key=lambda x: x["valoracion"], reverse=True)
        for j in lista:
            if len(eq1) < 8 and (val_eq(eq1) <= val_eq(eq2) or len(eq2) == 8):
                eq1.append(j)
            elif len(eq2) < 8: eq2.append(j)
            else: eq1.append(j)

    balancear_linea(arq_s)
    balancear_linea(def_s)
    balancear_linea(med_s)
    balancear_linea(del_s)

    # Ordenar resultados por ARQ-DEF-MED-DEL para mostrarlos prolijos
    prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
    eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
    eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

    # Imprimir en la interfaz
    texto_resultado.delete(1.0, tk.END)
    for i, eq in enumerate([eq1, eq2], 1):
        prom = val_eq(eq)/8 if len(eq) == 8 else 0
        texto_resultado.insert(tk.END, f"=== EQUIPO {i} (Promedio: {prom:.2f}) ===\n")
        for j in eq:
            sec_txt = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
            ami_txt = f" [Dúo: {j['amigo']}]" if j['amigo'] else ""
            texto_resultado.insert(tk.END, f" - {j['posicion']:^3} | {j['nombre']:<15} | Val: {j['valoracion']}{sec_txt}{ami_txt}\n")
        texto_resultado.insert(tk.END, "\n")

# ==========================================
# 4. INTERFAZ GRÁFICA (Ajustada)
# ==========================================

root = tk.Tk()
root.title("Gestor Piraña - Actualizado")
# root.iconbitmap("icono.ico") # Comentado temporalmente por si no tenés el archivo del ícono a mano
root.geometry("900x850")
inicializar_db()

# --- Frame Superior (Formulario) ---
f_top = tk.Frame(root, pady=10)
f_top.pack()

tk.Label(f_top, text="Nombre:").grid(row=0, column=0)
entry_nombre = tk.Entry(f_top, width=12)
entry_nombre.grid(row=0, column=1, padx=2)

tk.Label(f_top, text="Pos:").grid(row=0, column=2)
combo_posicion = ttk.Combobox(f_top, values=["ARQ", "DEF", "MED", "DEL"], width=5, state="readonly")
combo_posicion.set("MED")
combo_posicion.grid(row=0, column=3, padx=2)

tk.Label(f_top, text="Pos. Sec:").grid(row=0, column=4)
combo_secundaria = ttk.Combobox(f_top, values=["Ninguna", "ARQ", "DEF", "MED", "DEL"], width=8, state="readonly")
combo_secundaria.set("Ninguna")
combo_secundaria.grid(row=0, column=5, padx=2)

tk.Label(f_top, text="Val:").grid(row=0, column=6)
entry_valoracion = tk.Spinbox(f_top, from_=1, to=99, width=4)
entry_valoracion.grid(row=0, column=7, padx=2)

tk.Label(f_top, text="Amigo:").grid(row=0, column=8)
entry_amigo = tk.Entry(f_top, width=10)
entry_amigo.grid(row=0, column=9, padx=2)

# --- Frame Botones ---
f_mid = tk.Frame(root)
f_mid.pack(pady=5)
tk.Button(f_mid, text="Guardar", command=agregar_jugador, bg="#d4edda").pack(side="left", padx=5)
tk.Button(f_mid, text="Modificar", command=modificar_jugador, bg="#d1ecf1").pack(side="left", padx=5)
tk.Button(f_mid, text="Eliminar", command=eliminar_jugador, bg="#f8d7da").pack(side="left", padx=5)

# --- Tabla (Treeview) ---
tree = ttk.Treeview(root, columns=("N", "P", "PS", "V", "A"), show="headings", height=12)
for c, h in zip(("N", "P", "PS", "V", "A"), ("Nombre", "Pos", "Pos. Sec", "Val", "Dúo")): 
    tree.heading(c, text=h)
    tree.column(c, width=100 if c in ("P", "PS", "V") else 150, anchor="center" if c in ("P", "PS", "V") else "w")
tree.pack(fill="both", expand=True, padx=20)
tree.bind("<ButtonRelease-1>", cargar_formulario)

# --- Generador y Resultados ---
tk.Button(root, text="⚽ GENERAR PARTIDO (Seleccioná 16 con Ctrl+Clic) ⚽", font=("Arial", 12, "bold"), command=generar_equipos, bg="#fff3cd", pady=10).pack(fill="x", padx=20, pady=10)
texto_resultado = tk.Text(root, height=18, font=("Consolas", 10))
texto_resultado.pack(fill="both", padx=20, pady=10)

refrescar_tabla()
root.mainloop()