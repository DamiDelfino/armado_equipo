import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS
# ==========================================
def conectar_db():
    return sqlite3.connect("futbol_plantel.db")

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    # Agregamos la columna pos_secundaria a la tabla
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
    
    cursor.execute("SELECT COUNT(*) FROM jugadores")
    if cursor.fetchone()[0] == 0:
        # Actualizamos la lista inicial para incluir la posición secundaria ("Ninguna" por defecto)
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
        cursor.executemany("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (?, ?, ?, ?, ?)", plantel_inicial)
        conn.commit()
    conn.close()

# ==========================================
# 2. FUNCIÓN DE DIBUJO DE CANCHA
# ==========================================
def dibujar_cancha(equipo, titulo, color_puntos):
    posiciones_orden = ["ARQ", "DEF", "MED", "DEL"]
    coords_x = []
    coords_y = []
    nombres = []
    alturas = {"ARQ": 10, "DEF": 35, "MED": 65, "DEL": 90}

    for pos in posiciones_orden:
        jugadores_en_pos = [j for j in equipo if j["posicion"] == pos]
        n = len(jugadores_en_pos)
        for i, j in enumerate(jugadores_en_pos):
            x_pos = (i + 1) * (100 / (n + 1))
            coords_x.append(x_pos)
            coords_y.append(alturas[pos])
            nombres.append(f"{j['nombre']}<br>({j['valoracion']})")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=coords_x, y=coords_y, mode='markers+text', text=nombres, textposition="top center",
        marker=dict(size=25, color=color_puntos, line=dict(width=2, color='white')), textfont=dict(color='white', size=11)
    ))
    fig.update_layout(
        title=dict(text=titulo, font=dict(color='white', size=18), x=0.5),
        width=350, height=450, margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 110], showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#234721", paper_bgcolor="#1e1e1e", 
    )
    fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=15, line=dict(color="white")) 
    fig.add_shape(type="circle", x0=40, y0=95, x1=60, y1=105, line=dict(color="white")) 
    return fig

# ==========================================
# 3. CONFIGURACIÓN E INTERFAZ
# ==========================================
st.set_page_config(page_title="Fútbol 8 App", page_icon="⚽", layout="wide")
inicializar_db()

st.title("⚽ Armador de Equipos Equitativos")

# Leemos la base de datos al principio para usarla en los menús de edición y en la tabla
conn = conectar_db()
df_db = pd.read_sql("SELECT id, nombre, posicion, pos_secundaria, valoracion, amigo FROM jugadores ORDER BY nombre COLLATE NOCASE ASC", conn)
conn.close()

# --- PANEL 1: AGREGAR JUGADOR ---
with st.expander("➕ Agregar Nuevo Jugador"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4, c5 = st.columns(5)
        nombre_nuevo = c1.text_input("Nombre")
        pos_nuevo = c2.selectbox("Pos. Principal", ["ARQ", "DEF", "MED", "DEL"])
        sec_nuevo = c3.selectbox("Pos. Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"])
        val_nuevo = c4.number_input("Valoración", min_value=1, max_value=99, value=80)
        amigo_nuevo = c5.text_input("Dúo (opcional)")
        
        if st.form_submit_button("Guardar Jugador"):
            if nombre_nuevo:
                conn = conectar_db()
                conn.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (?, ?, ?, ?, ?)", 
                             (nombre_nuevo, pos_nuevo, sec_nuevo, val_nuevo, amigo_nuevo))
                conn.commit(); conn.close()
                st.success("¡Jugador agregado!")
                st.rerun()

# --- PANEL 2: MODIFICAR / ELIMINAR JUGADOR ---
with st.expander("✏️ Modificar o Eliminar Jugador Existente"):
    nombres_lista = df_db["nombre"].tolist()
    jugador_seleccionado = st.selectbox("Buscá el jugador que querés editar:", [""] + nombres_lista)

    if jugador_seleccionado:
        # Filtramos los datos del jugador elegido
        datos_jugador = df_db[df_db["nombre"] == jugador_seleccionado].iloc[0]
        id_jug = int(datos_jugador["id"])
        
        # Pre-rellenamos las opciones asegurándonos que coincidan con la lista
        opciones_pos = ["ARQ", "DEF", "MED", "DEL"]
        idx_pos = opciones_pos.index(datos_jugador["posicion"]) if datos_jugador["posicion"] in opciones_pos else 0
        
        opciones_sec = ["Ninguna", "ARQ", "DEF", "MED", "DEL"]
        idx_sec = opciones_sec.index(datos_jugador["pos_secundaria"]) if datos_jugador["pos_secundaria"] in opciones_sec else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        mod_nom = c1.text_input("Nombre", value=datos_jugador["nombre"], key="m_nom")
        mod_pos = c2.selectbox("Pos. Principal", opciones_pos, index=idx_pos, key="m_pos")
        mod_sec = c3.selectbox("Pos. Secundaria", opciones_sec, index=idx_sec, key="m_sec")
        mod_val = c4.number_input("Valoración", min_value=1, max_value=99, value=int(datos_jugador["valoracion"]), key="m_val")
        mod_amigo = c5.text_input("Dúo", value=str(datos_jugador["amigo"]) if pd.notna(datos_jugador["amigo"]) else "", key="m_ami")

        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("💾 Actualizar Datos", type="primary"):
            conn = conectar_db()
            conn.execute("UPDATE jugadores SET nombre=?, posicion=?, pos_secundaria=?, valoracion=?, amigo=? WHERE id=?", 
                         (mod_nom, mod_pos, mod_sec, mod_val, mod_amigo, id_jug))
            conn.commit(); conn.close()
            st.success("¡Datos actualizados correctamente!")
            st.rerun()
            
        if col_btn2.button("🗑️ Eliminar Jugador"):
            conn = conectar_db()
            conn.execute("DELETE FROM jugadores WHERE id=?", (id_jug,))
            conn.commit(); conn.close()
            st.error("¡Jugador eliminado del plantel!")
            st.rerun()

# --- PANEL 3: TABLA DE SELECCIÓN ---
st.subheader("Lista de Jugadores (Seleccioná a los 16)")

# Preparamos el DataFrame para mostrar
df_mostrar = df_db[["nombre", "posicion", "pos_secundaria", "valoracion", "amigo"]].copy()
df_mostrar.insert(0, "Selección", False)

tabla_editada = st.data_editor(
    df_mostrar,
    column_config={
        "Selección": st.column_config.CheckboxColumn("¿Juega?", default=False),
        "pos_secundaria": "Pos. Secundaria",
        "valoracion": st.column_config.ProgressColumn("Nivel", min_value=0, max_value=99, format="%d")
    },
    disabled=["nombre", "posicion", "pos_secundaria", "valoracion", "amigo"], 
    hide_index=True,
    use_container_width=True
)

convocados_raw = tabla_editada[tabla_editada["Selección"] == True]

# ==========================================
# 4. ALGORITMO Y RESULTADOS
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS BALANCEADOS", type="primary", use_container_width=True):
    
    if len(convocados_raw) != 16:
        st.error(f"⚠️ Selección incorrecta: Tenés {len(convocados_raw)} de 16 jugadores necesarios.")
    else:
        convocados = []
        for _, row in convocados_raw.iterrows():
            amigo_val = str(row["amigo"]) if pd.notna(row["amigo"]) and str(row["amigo"]) != "" else ""
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
                "pos_secundaria": str(row["pos_secundaria"]),
                "valoracion": int(row["valoracion"]), 
                "amigo": amigo_val
            })

        procesados = set()
        grupos = []
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

        grupos_amigos = [g for g in grupos_restantes if len(g) > 1]
        grupos_solos = [g for g in grupos_restantes if len(g) == 1]

        def val_eq(e): return sum(x["valoracion"] for x in e)

        grupos_amigos.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
        for g in grupos_amigos:
            if len(eq1) + len(g) <= 8 and (val_eq(eq1) <= val_eq(eq2) or len(eq2) == 8):
                eq1.extend(g)
            else: eq2.extend(g)

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

        prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
        eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

        # --- MOSTRAR RESULTADOS ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            prom1 = val_eq(eq1)/8 if len(eq1)==8 else 0
            st.success("🔵 EQUIPO 1")
            st.plotly_chart(dibujar_cancha(eq1, f"Promedio: {prom1:.2f}", "#3498db"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq1: 
                    # Agregamos la vista de la posición secundaria si es que tiene
                    sec_txt = f" *(Sec: {j['pos_secundaria']})*" if j['pos_secundaria'] != "Ninguna" else ""
                    ami_txt = f" *(Dúo: {j['amigo']})*" if j['amigo'] else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']} ({j['valoracion']}){sec_txt}{ami_txt}")

        with col2:
            prom2 = val_eq(eq2)/8 if len(eq2)==8 else 0
            st.warning("🟠 EQUIPO 2")
            st.plotly_chart(dibujar_cancha(eq2, f"Promedio: {prom2:.2f}", "#e67e22"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq2: 
                    sec_txt = f" *(Sec: {j['pos_secundaria']})*" if j['pos_secundaria'] != "Ninguna" else ""
                    ami_txt = f" *(Dúo: {j['amigo']})*" if j['amigo'] else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']} ({j['valoracion']}){sec_txt}{ami_txt}")