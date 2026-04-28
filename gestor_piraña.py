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
            valoracion INTEGER NOT NULL,
            amigo TEXT
        )
    ''')
    
    
    # Verificamos si está vacía para cargar los 30 por defecto
    cursor.execute("SELECT COUNT(*) FROM jugadores")
    if cursor.fetchone()[0] == 0:
        plantel_inicial = [
            ("Tucu", "DEF", 82,""), ("Fabi", "DEF", 81,""), ("Ale", "MED", 71,""),
            ("Dami", "DEF", 79,""), ("Martn", "MED", 84,""), ("Cesar", "MED", 79,""),
            ("Giorgio", "MED", 81,""), ("Santiago", "DEL", 84,""), ("Toro", "ARQ", 80,""),
            ("Pipino", "MED", 81,""), ("Pablito", "MED", 82,""), ("Chapa", "MED", 80,""),
            ("Rodri", "DEL", 79,""), ("Pasteles", "DEL", 78,""), ("Tojo", "DEF", 77,""),
            ("Pitu", "DEF", 78,""), ("Gusti", "MED", 75,""), ("Lucho", "DEL", 70,""),
            ("Chizzo", "DEL", 60,""), ("Facu Amorena", "DEL", 73,""), ("Edgar", "DEF", 80,""),
            ("Gonza", "DEF", 79,""), ("Fer", "MED", 80,""), ("Nico", "DEL", 77,""),
            ("Brian", "MED", 73,""), ("Agustiki", "DEL", 80,""), ("David", "MED", 82,"Santiago"),
            ("Nacho", "DEF", 81,""),("Mario", "MED", 80, "Cesar")
        ]
        cursor.executemany("INSERT INTO jugadores (nombre, posicion, valoracion, amigo) VALUES (?, ?, ?, ?)", plantel_inicial)
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
    # MEJORA: Orden alfabético en la grilla principal
    cursor.execute("SELECT * FROM jugadores ORDER BY nombre COLLATE NOCASE ASC")
    for row in cursor.fetchall():
        tree.insert("", tk.END, iid=row[0], values=(row[1], row[2], row[3], row[4]))
    conn.close()

def agregar_jugador():
    nombre = entry_nombre.get().strip()
    posicion = combo_posicion.get()
    valoracion = entry_valoracion.get()
    amigo = entry_amigo.get().strip()
    if not nombre or not valoracion: return
    conn = conectar_db(); cursor = conn.cursor()
    cursor.execute("INSERT INTO jugadores (nombre, posicion, valoracion, amigo) VALUES (?, ?, ?, ?)", (nombre, posicion, valoracion, amigo))
    conn.commit(); conn.close()
    refrescar_tabla(); limpiar_formulario()

def modificar_jugador():
    seleccion = tree.selection()
    if not seleccion: return
    conn = conectar_db(); cursor = conn.cursor()
    cursor.execute("UPDATE jugadores SET nombre=?, posicion=?, valoracion=?, amigo=? WHERE id=?", 
                   (entry_nombre.get(), combo_posicion.get(), entry_valoracion.get(), entry_amigo.get(), seleccion[0]))
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
    entry_nombre.delete(0, tk.END); entry_valoracion.delete(0, tk.END); entry_amigo.delete(0, tk.END)

def cargar_formulario(event):
    seleccion = tree.selection()
    if seleccion:
        v = tree.item(seleccion[0])['values']
        limpiar_formulario()
        entry_nombre.insert(0, v[0]); combo_posicion.set(v[1]); entry_valoracion.insert(0, v[2])
        entry_amigo.insert(0, v[3] if v[3] != "None" else "")

# ==========================================
# 3. BALANCEO Y ORDEN POSICIONAL
# ==========================================

def generar_equipos():
    seleccionados = tree.selection()
    if len(seleccionados) != 16:
        messagebox.showwarning("Error", f"Seleccioná 16. Van: {len(seleccionados)}")
        return

    convocados = []
    for item_id in seleccionados:
        v = tree.item(item_id)['values']
        convocados.append({"nombre": str(v[0]), "posicion": str(v[1]), "valoracion": int(v[2]), "amigo": str(v[3]) if v[3] != "None" else ""})

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
    # Compensación de arquero único
    arqs = [j for j in convocados if j["posicion"] == "ARQ"]
    if len(arqs) == 1:
        g_arq = next(g for g in grupos if any(x["posicion"]=="ARQ" for x in g))
        eq1.extend(g_arq); grupos.remove(g_arq)
        sin_arq = [g for g in grupos if not any(x["posicion"]=="ARQ" for x in g)]
        m_def_g = max(sin_arq, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
        eq2.extend(m_def_g); grupos.remove(m_def_g)

    grupos.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
    for g in grupos:
        if len(eq1) + len(g) <= 8 and (sum(x["valoracion"] for x in eq1) <= sum(x["valoracion"] for x in eq2) or len(eq2) == 8):
            eq1.extend(g)
        else: eq2.extend(g)

    # MEJORA: Ordenar resultados por ARQ-DEF-MED-DEL
    prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
    eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
    eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

    texto_resultado.delete(1.0, tk.END)
    for i, eq in enumerate([eq1, eq2], 1):
        prom = sum(x["valoracion"] for x in eq)/8
        texto_resultado.insert(tk.END, f"=== EQUIPO {i} (Promedio: {prom:.2f}) ===\n")
        for j in eq:
            texto_resultado.insert(tk.END, f" - {j['posicion']:^3} | {j['nombre']:<15} | Val: {j['valoracion']}\n")
        texto_resultado.insert(tk.END, "\n")

# ==========================================
# 4. INTERFAZ
# ==========================================

root = tk.Tk()
root.title("Fútbol 8 - Orden y Amigos")
root.iconbitmap("icono.ico")
root.geometry("800x850")
inicializar_db()

f_top = tk.Frame(root, pady=10); f_top.pack()
tk.Label(f_top, text="Nombre:").grid(row=0, column=0)
entry_nombre = tk.Entry(f_top, width=15); entry_nombre.grid(row=0, column=1, padx=5)
tk.Label(f_top, text="Pos:").grid(row=0, column=2)
combo_posicion = ttk.Combobox(f_top, values=["ARQ", "DEF", "MED", "DEL"], width=5, state="readonly"); combo_posicion.set("MED"); combo_posicion.grid(row=0, column=3, padx=5)
tk.Label(f_top, text="Val:").grid(row=0, column=4)
entry_valoracion = tk.Spinbox(f_top, from_=1, to=99, width=5); entry_valoracion.grid(row=0, column=5, padx=5)
tk.Label(f_top, text="Amigo:").grid(row=0, column=6)
entry_amigo = tk.Entry(f_top, width=12); entry_amigo.grid(row=0, column=7, padx=5)

f_mid = tk.Frame(root); f_mid.pack(pady=5)
tk.Button(f_mid, text="Guardar", command=agregar_jugador, bg="#d4edda").pack(side="left", padx=5)
tk.Button(f_mid, text="Modificar", command=modificar_jugador, bg="#d1ecf1").pack(side="left", padx=5)
tk.Button(f_mid, text="Eliminar", command=eliminar_jugador, bg="#f8d7da").pack(side="left", padx=5)

tree = ttk.Treeview(root, columns=("N", "P", "V", "A"), show="headings", height=12)
for c, h in zip(("N", "P", "V", "A"), ("Nombre", "Pos", "Val", "Dúo")): 
    tree.heading(c, text=h); tree.column(c, width=100, anchor="center" if c in ("P","V") else "w")
tree.pack(fill="both", expand=True, padx=20); tree.bind("<ButtonRelease-1>", cargar_formulario)

tk.Button(root, text="⚽ GENERAR PARTIDO (Seleccionar 16) ⚽", font=("Arial", 12, "bold"), command=generar_equipos, bg="#fff3cd", pady=10).pack(fill="x", padx=20, pady=10)
texto_resultado = tk.Text(root, height=15, font=("Consolas", 10)); texto_resultado.pack(fill="both", padx=20, pady=10)

refrescar_tabla()
root.mainloop()
