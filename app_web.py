import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import psycopg2 # Cambiamos sqlite3 por psycopg2 para la nube

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS (SUPABASE)
# ==========================================
def conectar_db():
    # Streamlit busca automáticamente la variable que guardaste en Secrets
    return psycopg2.connect(st.secrets["DATABASE_URL"])

# Ya no necesitamos inicializar_db porque la tabla ya vive en la nube.

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
            # Etiqueta limpia sin valoración para compartir
            nombres.append(f"{j['nombre']}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=coords_x, y=coords_y, mode='markers+text', text=nombres, textposition="top center",
        marker=dict(size=25, color=color_puntos, line=dict(width=2, color='white')), 
        textfont=dict(color='white', size=13)
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

st.title("⚽ Armador de Equipos Equitativos")

# Lectura de la base de datos en Supabase
try:
    conn = conectar_db()
    # En Postgres usamos el mismo SQL, pero leemos con Pandas
    df_db = pd.read_sql("SELECT id, nombre, posicion, pos_secundaria, valoracion, amigo FROM jugadores ORDER BY nombre COLLATE \"C\" ASC", conn)
    conn.close()
except Exception as e:
    st.error(f"Error de conexión a la base de datos: {e}")
    st.stop()

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
                cur = conn.cursor()
                # CAMBIO: Usamos %s para PostgreSQL
                cur.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (%s, %s, %s, %s, %s)", 
                             (nombre_nuevo, pos_nuevo, sec_nuevo, val_nuevo, amigo_nuevo))
                conn.commit()
                cur.close()
                conn.close()
                st.success("¡Jugador agregado!")
                st.rerun()

# --- PANEL 2: MODIFICAR / ELIMINAR JUGADOR ---
with st.expander("✏️ Modificar o Eliminar Jugador Existente"):
    nombres_lista = df_db["nombre"].tolist()
    jugador_seleccionado = st.selectbox("Buscá el jugador que querés editar:", [""] + nombres_lista)

    if jugador_seleccionado:
        datos_jugador = df_db[df_db["nombre"] == jugador_seleccionado].iloc[0]
        id_jug = int(datos_jugador["id"])
        
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
            cur = conn.cursor()
            cur.execute("UPDATE jugadores SET nombre=%s, posicion=%s, pos_secundaria=%s, valoracion=%s, amigo=%s WHERE id=%s", 
                         (mod_nom, mod_pos, mod_sec, mod_val, mod_amigo, id_jug))
            conn.commit(); cur.close(); conn.close()
            st.success("¡Datos actualizados!")
            st.rerun()
            
        if col_btn2.button("🗑️ Eliminar Jugador"):
            conn = conectar_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM jugadores WHERE id=%s", (id_jug,))
            conn.commit(); cur.close(); conn.close()
            st.error("¡Jugador eliminado!")
            st.rerun()

# --- PANEL 3: TABLA DE SELECCIÓN ---
st.subheader("Lista de Jugadores (Seleccioná a los 16)")
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
# 4. ALGORITMO BALANCEADO (ESPEJO + OPTIMIZACIÓN)
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS BALANCEADOS", type="primary", use_container_width=True):
    
    if len(convocados_raw) != 16:
        st.error(f"⚠️ Selección incorrecta: Tenés {len(convocados_raw)} de 16 jugadores necesarios.")
    else:
        convocados = []
        for _, row in convocados_raw.iterrows():
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
                "pos_secundaria": str(row["pos_secundaria"]),
                "valoracion": int(row["valoracion"]), 
                "amigo": str(row["amigo"]) if pd.notna(row["amigo"]) else ""
            })

        def val_eq(e): return sum(x["valoracion"] for x in e)

        procesados = set(); grupos = []
        for j in convocados:
            if j["nombre"] in procesados: continue
            g = [j]; procesados.add(j["nombre"])
            if j["amigo"]:
                amigo = next((x for x in convocados if x["nombre"] == j["amigo"] and x["nombre"] not in procesados), None)
                if amigo: g.append(amigo); procesados.add(amigo["nombre"])
            grupos.append(g)

        eq1, eq2 = [], []
        arqs = [j for j in convocados if j["posicion"] == "ARQ"]
        grupos_con_arq = [g for g in grupos if any(x["posicion"] == "ARQ" for x in g)]
        grupos_sin_arq = [g for g in grupos if not any(x["posicion"] == "ARQ" for x in g)]
        
        if len(arqs) == 2 and len(grupos_con_arq) >= 2:
            eq1.extend(grupos_con_arq[0]); eq2.extend(grupos_con_arq[1])
            grupos_restantes = grupos_sin_arq
        else:
            grupos_restantes = grupos

        grupos_amigos = [g for g in grupos_restantes if len(g) > 1]
        grupos_solos = [g for g in grupos_restantes if len(g) == 1]
        
        for g in sorted(grupos_amigos, key=lambda x: sum(j["valoracion"] for j in x), reverse=True):
            if val_eq(eq1) <= val_eq(eq2) and len(eq1) + len(g) <= 8: eq1.extend(g)
            else: eq2.extend(g)

        solos = [g[0] for g in grupos_solos]
        for pos in ["DEF", "MED", "DEL", "ARQ"]:
            linea = sorted([j for j in solos if j["posicion"] == pos], key=lambda x: x["valoracion"], reverse=True)
            for i in range(0, len(linea), 2):
                par = linea[i:i+2]
                if len(par) == 2:
                    if val_eq(eq1) <= val_eq(eq2): eq1.append(par[0]); eq2.append(par[1])
                    else: eq2.append(par[0]); eq1.append(par[1])
                elif len(par) == 1:
                    if val_eq(eq1) <= val_eq(eq2): eq1.append(par[0])
                    else: eq2.append(par[0])

        # --- MOSTRAR RESULTADOS ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("🔵 EQUIPO 1")
            st.plotly_chart(dibujar_cancha(eq1, f"Balanceado ✅", "#3498db"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq1: 
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']}{sec}")

        with col2:
            st.warning("🟠 EQUIPO 2")
            st.plotly_chart(dibujar_cancha(eq2, f"Balanceado ✅", "#e67e22"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq2: 
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']}{sec}")