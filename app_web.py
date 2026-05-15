import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import psycopg2

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS (NUBE - SUPABASE)
# ==========================================
def conectar_db():
    # Asegurate de tener DATABASE_URL en los Secrets de Streamlit
    return psycopg2.connect(st.secrets["DATABASE_URL"])

# ==========================================
# 2. FUNCIÓN DE DIBUJO DE CANCHA
# ==========================================
def dibujar_cancha(equipo, titulo, color_puntos):
    posiciones_orden = ["ARQ", "DEF", "MED", "DEL"]
    coords_x, coords_y, nombres = [], [], []
    alturas = {"ARQ": 10, "DEF": 35, "MED": 65, "DEL": 90}

    for pos in posiciones_orden:
        jugadores_en_pos = [j for j in equipo if j["posicion"] == pos]
        n = len(jugadores_en_pos)
        for i, j in enumerate(jugadores_en_pos):
            x_pos = (i + 1) * (100 / (n + 1))
            coords_x.append(x_pos)
            coords_y.append(alturas[pos])
            # Etiqueta limpia para las capturas de pantalla
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
# 3. INTERFAZ Y LECTURA DE DATOS
# ==========================================
st.set_page_config(page_title="Fútbol 8 App", page_icon="⚽", layout="wide")
st.title("⚽ Armador de Equipos Equitativos")

try:
    conn = conectar_db()
    df_db = pd.read_sql('SELECT id, nombre, posicion, pos_secundaria, valoracion, amigo FROM jugadores ORDER BY LOWER(nombre) ASC', conn)
    conn.close()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

with st.expander("➕ Agregar Nuevo Jugador"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4, c5 = st.columns(5)
        n_nuevo = c1.text_input("Nombre")
        p_nuevo = c2.selectbox("Pos. Principal", ["ARQ", "DEF", "MED", "DEL"])
        s_nuevo = c3.selectbox("Pos. Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"])
        v_nuevo = c4.number_input("Valoración", 1, 99, 80)
        a_nuevo = c5.text_input("Dúo (opcional)")
        if st.form_submit_button("Guardar"):
            if n_nuevo:
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, valoracion, amigo) VALUES (%s, %s, %s, %s, %s)", 
                             (n_nuevo, p_nuevo, s_nuevo, v_nuevo, a_nuevo))
                conn.commit(); cur.close(); conn.close(); st.rerun()

with st.expander("✏️ Modificar o Eliminar Jugador"):
    nom_lista = df_db["nombre"].tolist()
    j_sel = st.selectbox("Elegí un jugador:", [""] + nom_lista)
    if j_sel:
        dat = df_db[df_db["nombre"] == j_sel].iloc[0]
        id_j = int(dat["id"])
        c1, c2, c3, c4, c5 = st.columns(5)
        m_nom = c1.text_input("Nombre", value=dat["nombre"])
        m_pos = c2.selectbox("Pos. Principal", ["ARQ", "DEF", "MED", "DEL"], index=["ARQ", "DEF", "MED", "DEL"].index(dat["posicion"]))
        m_sec = c3.selectbox("Pos. Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"], index=["Ninguna", "ARQ", "DEF", "MED", "DEL"].index(dat["pos_secundaria"]))
        m_val = c4.number_input("Valoración", 1, 99, int(dat["valoracion"]))
        m_ami = c5.text_input("Dúo", value=str(dat["amigo"]) if pd.notna(dat["amigo"]) else "")
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("💾 Actualizar"):
            conn = conectar_db(); cur = conn.cursor()
            cur.execute("UPDATE jugadores SET nombre=%s, posicion=%s, pos_secundaria=%s, valoracion=%s, amigo=%s WHERE id=%s", (m_nom, m_pos, m_sec, m_val, m_ami, id_j))
            conn.commit(); cur.close(); conn.close(); st.rerun()
        if col_b2.button("🗑️ Eliminar"):
            conn = conectar_db(); cur = conn.cursor()
            cur.execute("DELETE FROM jugadores WHERE id=%s", (id_j,)); conn.commit(); cur.close(); conn.close(); st.rerun()

st.subheader("Seleccioná los 16 del partido")
df_edit = df_db[["nombre", "posicion", "pos_secundaria", "valoracion", "amigo"]].copy()
df_edit.insert(0, "Selección", False)
tab_edit = st.data_editor(df_edit, column_config={"Selección": st.column_config.CheckboxColumn("¿Juega?", default=False), "valoracion": st.column_config.ProgressColumn("Nivel", 0, 99, "%d")}, disabled=["nombre", "posicion", "pos_secundaria", "valoracion", "amigo"], hide_index=True, use_container_width=True)
conv_raw = tab_edit[tab_edit["Selección"] == True]

# ==========================================
# 4. ALGORITMO CORRECTO (VÍNCULOS BIDIRECCIONALES)
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS", type="primary", use_container_width=True):
    if len(conv_raw) != 16:
        st.error(f"Faltan jugadores. Tenés {len(conv_raw)} de 16.")
    else:
        convocados = []
        for _, row in conv_raw.iterrows():
            convocados.append({"nombre": str(row["nombre"]), "posicion": str(row["posicion"]), "pos_secundaria": str(row["pos_secundaria"]), "valoracion": int(row["valoracion"]), "amigo": str(row["amigo"]) if pd.notna(row["amigo"]) else ""})

        def val_eq(e): return sum(x["valoracion"] for x in e)

        # AGRUPACIÓN CORREGIDA
        procesados = set(); grupos = []
        for j in convocados:
            if j["nombre"] in procesados: continue
            g = [j]; procesados.add(j["nombre"])
            # 1. Vínculo directo (A tiene a B)
            if j["amigo"]:
                amigo = next((x for x in convocados if x["nombre"] == j["amigo"] and x["nombre"] not in procesados), None)
                if amigo: g.append(amigo); procesados.add(amigo["nombre"])
            # 2. Vínculo inverso (Alguien tiene a A)
            inv = next((x for x in convocados if x["amigo"] == j["nombre"] and x["nombre"] not in procesados), None)
            if inv: g.append(inv); procesados.add(inv["nombre"])
            grupos.append(g)

        eq1, eq2 = [], []
        # Reparto de Arqueros
        arqs_g = [g for g in grupos if any(x["posicion"] == "ARQ" for x in g)]
        if len(arqs_g) >= 2:
            eq1.extend(arqs_g[0]); eq2.extend(arqs_g[1])
            grupos = [g for g in grupos if g not in arqs_g]
        elif len(arqs_g) == 1:
            eq1.extend(arqs_g[0]); grupos.remove(arqs_g[0])
            libres = [g for g in grupos if not any(x["posicion"] == "ARQ" for x in g)]
            if libres:
                m_def = max(libres, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
                eq2.extend(m_def); grupos.remove(m_def)

        # Reparto de Amigos (Dúos)
        g_amigos = sorted([g for g in grupos if len(g) > 1], key=lambda x: sum(j["valoracion"] for j in x), reverse=True)
        for g in g_amigos:
            if val_eq(eq1) <= val_eq(eq2) and len(eq1) + len(g) <= 8: eq1.extend(g)
            else: eq2.extend(g)
        
        # Reparto Espejo de individuales por línea
        solos = [g[0] for g in grupos if len(g) == 1 and g[0] not in eq1 and g[0] not in eq2]
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

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.success("🔵 EQUIPO 1")
            st.plotly_chart(dibujar_cancha(eq1, "Balanceado ✅", "#3498db"), use_container_width=True)
            with st.expander("Lista"):
                for j in eq1:
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']}{sec}")
        with col2:
            st.warning("🟠 EQUIPO 2")
            st.plotly_chart(dibujar_cancha(eq2, "Balanceado ✅", "#e67e22"), use_container_width=True)
            with st.expander("Lista"):
                for j in eq2:
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']}{sec}")