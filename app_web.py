import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import psycopg2

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS Y LÓGICA EA FC
# ==========================================
def conectar_db():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def calcular_media_global(pos, rit, tir, pas, reg, _def, fis):
    """Fórmula matemática ponderada estilo EA FC 25."""
    if pos == "DEF":
        val = (rit * 0.10) + (tir * 0.00) + (pas * 0.15) + (reg * 0.05) + (_def * 0.50) + (fis * 0.20)
    elif pos == "MED":
        val = (rit * 0.10) + (tir * 0.15) + (pas * 0.35) + (reg * 0.20) + (_def * 0.10) + (fis * 0.10)
    elif pos == "DEL":
        val = (rit * 0.20) + (tir * 0.40) + (pas * 0.10) + (reg * 0.15) + (_def * 0.00) + (fis * 0.15)
    elif pos == "ARQ":
        val = (rit * 0.10) + (tir * 0.00) + (pas * 0.20) + (reg * 0.00) + (_def * 0.60) + (fis * 0.10)
    else: val = 75
    return round(val)

# ==========================================
# 2. FUNCIÓN DE DIBUJO DE CANCHA (VISTA LIMPIA)
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
            coords_x.append(x_pos); coords_y.append(alturas[pos])
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
# 3. INTERFAZ WEB
# ==========================================
st.set_page_config(page_title="Fútbol 8 Pro", page_icon="⚽", layout="wide")
st.title("⚽ Armador de Equipos EA FC")

try:
    conn = conectar_db()
    df_db = pd.read_sql('SELECT * FROM jugadores ORDER BY LOWER(nombre) ASC', conn)
    conn.close()
    
    df_db['valoracion_real'] = df_db.apply(lambda r: calcular_media_global(
        r['posicion'], r['ritmo'], r['tiro'], r['pase'], r['regate'], r['defensa'], r['fisico']
    ), axis=1)
    
except Exception as e:
    st.error(f"Error de base de datos: {e}"); st.stop()

# --- PANEL 1: AGREGAR JUGADOR ---
with st.expander("➕ Nuevo Jugador (Cargar Stats)"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4 = st.columns(4)
        n_n = c1.text_input("Nombre")
        p_n = c2.selectbox("Posición", ["ARQ", "DEF", "MED", "DEL"])
        s_n = c3.selectbox("Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"])
        a_n = c4.text_input("Dúo")
        
        st.write("Atributos Físicos/Técnicos:")
        at1, at2, at3, at4, at5, at6 = st.columns(6)
        rit = at1.number_input("RIT", 1, 99, 75)
        tir = at2.number_input("TIR", 1, 99, 75)
        pas = at3.number_input("PAS", 1, 99, 75)
        reg = at4.number_input("REG", 1, 99, 75)
        _df = at5.number_input("DEF", 1, 99, 75)
        fis = at6.number_input("FIS", 1, 99, 75)
        
        if st.form_submit_button("Guardar en Supabase"):
            if n_n:
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, amigo, ritmo, tiro, pase, regate, defensa, fisico) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                             (n_n, p_n, s_n, a_n, rit, tir, pas, reg, _df, fis))
                conn.commit(); cur.close(); conn.close(); st.rerun()

# --- PANEL 2: MODIFICAR JUGADOR ---
with st.expander("✏️ Editar Atributos de Jugador"):
    j_sel = st.selectbox("Elegí a quién editar:", [""] + df_db["nombre"].tolist())
    if j_sel:
        d = df_db[df_db["nombre"] == j_sel].iloc[0]
        with st.form("form_edit"):
            c1, c2, c3, c4 = st.columns(4)
            m_nom = c1.text_input("Nombre", value=d["nombre"])
            m_pos = c2.selectbox("Posición", ["ARQ", "DEF", "MED", "DEL"], index=["ARQ", "DEF", "MED", "DEL"].index(d["posicion"]))
            m_sec = c3.selectbox("Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"], index=["Ninguna", "ARQ", "DEF", "MED", "DEL"].index(d["pos_secundaria"]))
            m_ami = c4.text_input("Dúo", value=str(d["amigo"]) if d["amigo"] else "")
            
            at1, at2, at3, at4, at5, at6 = st.columns(6)
            m_rit = at1.number_input("RIT", 1, 99, int(d["ritmo"]))
            m_tir = at2.number_input("TIR", 1, 99, int(d["tiro"]))
            m_pas = at3.number_input("PAS", 1, 99, int(d["pase"]))
            m_reg = at4.number_input("REG", 1, 99, int(d["regate"]))
            m_df  = at5.number_input("DEF", 1, 99, int(d["defensa"]))
            m_fis = at6.number_input("FIS", 1, 99, int(d["fisico"]))
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("💾 Actualizar"):
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("UPDATE jugadores SET nombre=%s, posicion=%s, pos_secundaria=%s, amigo=%s, ritmo=%s, tiro=%s, pase=%s, regate=%s, defensa=%s, fisico=%s WHERE id=%s", (m_nom, m_pos, m_sec, m_ami, m_rit, m_tir, m_pas, m_reg, m_df, m_fis, int(d["id"])))
                conn.commit(); cur.close(); conn.close(); st.rerun()
            if col_b2.form_submit_button("🗑️ Eliminar"):
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("DELETE FROM jugadores WHERE id=%s", (int(d["id"]),)); conn.commit(); cur.close(); conn.close(); st.rerun()

# --- PANEL 3: TABLA DE SELECCIÓN ---
st.subheader("Seleccioná los 16 del partido")
df_edit = df_db[["nombre", "posicion", "pos_secundaria", "valoracion_real", "amigo"]].copy()
df_edit.insert(0, "Selección", False)

tab_edit = st.data_editor(
    df_edit, 
    column_config={
        "Selección": st.column_config.CheckboxColumn("¿Juega?"),
        "valoracion_real": st.column_config.ProgressColumn("Nivel EA FC", min_value=0, max_value=99, format="%d")
    }, 
    disabled=["nombre", "posicion", "pos_secundaria", "valoracion_real", "amigo"], 
    hide_index=True, use_container_width=True
)

conv_raw = tab_edit[tab_edit["Selección"] == True]

# ==========================================
# 4. ALGORITMO ESPEJO + OPTIMIZACIÓN (CORREGIDO)
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS BALANCEADOS", type="primary", use_container_width=True):
    if len(conv_raw) != 16:
        st.error(f"Faltan jugadores. Tenés {len(conv_raw)} de 16.")
    else:
        convocados = []
        for _, row in conv_raw.iterrows():
            convocados.append({"nombre": str(row["nombre"]), "posicion": str(row["posicion"]), "pos_secundaria": str(row["pos_secundaria"]), "valoracion": int(row["valoracion_real"]), "amigo": str(row["amigo"]) if pd.notna(row["amigo"]) else ""})

        def val_eq(e): return sum(x["valoracion"] for x in e)

        # Agrupación bidireccional por amigos
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
        
        # 4.1 Reparto de Arqueros y compensación inicial
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

        # 4.2 AGREGADO: Reparto de Bloques de Amigos (Dúos)
        g_amigos = sorted([g for g in grupos if len(g) > 1], key=lambda x: sum(j["valoracion"] for j in x), reverse=True)
        for g in g_amigos:
            if val_eq(eq1) <= val_eq(eq2) and len(eq1) + len(g) <= 8: eq1.extend(g)
            else: eq2.extend(g)

        # 4.3 Reparto Espejo de individuales por línea (Filtro corregido)
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

        # 4.4 AGREGADO: Post-Optimización fina por intercambios tácticos
        nombres_amigos = set(j["nombre"] for g in g_amigos for j in g)
        mejoro = True
        while mejoro:
            mejoro = False
            diff = abs(val_eq(eq1) - val_eq(eq2))
            for j1 in [x for x in eq1 if x["nombre"] not in nombres_amigos and x["posicion"] != "ARQ"]:
                for j2 in [x for x in eq2 if x["nombre"] not in nombres_amigos and x["posicion"] != "ARQ"]:
                    if j1["posicion"] == j2["posicion"]:
                        n_diff = abs((val_eq(eq1)-j1["valoracion"]+j2["valoracion"]) - (val_eq(eq2)-j2["valoracion"]+j1["valoracion"]))
                        if n_diff < diff:
                            eq1.remove(j1); eq1.append(j2)
                            eq2.remove(j2); eq2.append(j1)
                            diff = n_diff; mejoro = True; break
                if mejoro: break

        # Orden final visual por líneas
        prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
        eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

        # --- MOSTRAR RESULTADOS ---
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