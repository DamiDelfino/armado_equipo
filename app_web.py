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
st.set_page_config(page_title="Fútbol Piraña", page_icon="⚽", layout="wide")
st.title("⚽ Armador de Equipos Piraña")

formato_partido = st.selectbox(
    "Seleccioná el formato del partido:",
    ["Fútbol 5 (10 jugadores)", "Fútbol 7 (14 jugadores)", "Fútbol 8 (16 jugadores)", "Fútbol 9 (18 jugadores)"],
    index=2
)
cupo_total = int(formato_partido.split("(")[1].split()[0])
limite_eq = cupo_total // 2

try:
    conn = conectar_db()
    df_db = pd.read_sql('SELECT * FROM jugadores ORDER BY LOWER(nombre) ASC', conn)
    conn.close()
    
    df_db['valoracion_real'] = df_db.apply(lambda r: calcular_media_global(
        r['posicion'], r['ritmo'], r['tiro'], r['pase'], r['regate'], r['defensa'], r['fisico']
    ), axis=1)
except Exception as e:
    st.error(f"Error de base de datos: {e}"); st.stop()

with st.expander("➕ Nuevo Jugador (Cargar Stats)"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4, c5 = st.columns(5) # Añadimos una columna para Rol
        n_n = c1.text_input("Nombre")
        p_n = c2.selectbox("Posición", ["ARQ", "DEF", "MED", "DEL"])
        s_n = c3.selectbox("Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"])
        r_n = c4.selectbox("Rol", ["Mixto", "Ofensivo", "Defensivo"])
        a_n = c5.text_input("Dúo")
        
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
                cur.execute("INSERT INTO jugadores (nombre, posicion, pos_secundaria, amigo, ritmo, tiro, pase, regate, defensa, fisico, valoracion, rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                             (n_n, p_n, s_n, a_n, rit, tir, pas, reg, _df, fis, 75, r_n))
                conn.commit(); cur.close(); conn.close(); st.rerun()

with st.expander("✏️ Editar Atributos de Jugador"):
    j_sel = st.selectbox("Elegí a quién editar:", [""] + df_db["nombre"].tolist())
    if j_sel:
        d = df_db[df_db["nombre"] == j_sel].iloc[0]
        with st.form("form_edit"):
            c1, c2, c3, c4, c5 = st.columns(5)
            m_nom = c1.text_input("Nombre", value=d["nombre"])
            m_pos = c2.selectbox("Posición", ["ARQ", "DEF", "MED", "DEL"], index=["ARQ", "DEF", "MED", "DEL"].index(d["posicion"]))
            m_sec = c3.selectbox("Secundaria", ["Ninguna", "ARQ", "DEF", "MED", "DEL"], index=["Ninguna", "ARQ", "DEF", "MED", "DEL"].index(d["pos_secundaria"]))
            
            # Control por si algún jugador viejo no tiene rol cargado
            rol_actual = d["rol"] if pd.notna(d["rol"]) else "Mixto"
            idx_rol = ["Mixto", "Ofensivo", "Defensivo"].index(rol_actual) if rol_actual in ["Mixto", "Ofensivo", "Defensivo"] else 0
            m_rol = c4.selectbox("Rol", ["Mixto", "Ofensivo", "Defensivo"], index=idx_rol)
            
            m_ami = c5.text_input("Dúo", value=str(d["amigo"]) if d["amigo"] else "")
            
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
                cur.execute("UPDATE jugadores SET nombre=%s, posicion=%s, pos_secundaria=%s, amigo=%s, ritmo=%s, tiro=%s, pase=%s, regate=%s, defensa=%s, fisico=%s, rol=%s WHERE id=%s", 
                            (m_nom, m_pos, m_sec, m_ami, m_rit, m_tir, m_pas, m_reg, m_df, m_fis, m_rol, int(d["id"])))
                conn.commit(); cur.close(); conn.close(); st.rerun()
            if col_b2.form_submit_button("🗑️ Eliminar"):
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("DELETE FROM jugadores WHERE id=%s", (int(d["id"]),)); conn.commit(); cur.close(); conn.close(); st.rerun()

st.subheader(f"Seleccioná {cupo_total} jugadores")
df_edit = df_db[["nombre", "posicion", "pos_secundaria", "rol", "valoracion_real", "amigo", "ritmo", "defensa"]].copy()
df_edit.insert(0, "Selección", False)

tab_edit = st.data_editor(
    df_edit, 
    column_config={
        "Selección": st.column_config.CheckboxColumn("¿Juega?"), 
        "valoracion_real": st.column_config.ProgressColumn("Nivel EA FC", min_value=0, max_value=99, format="%d"),
        "ritmo": None,   
        "defensa": None  
    }, 
    disabled=["nombre", "posicion", "pos_secundaria", "rol", "valoracion_real", "amigo"], hide_index=True, use_container_width=True
)
conv_raw = tab_edit[tab_edit["Selección"] == True]

# ==========================================
# 4. ALGORITMO TÁCTICO + QUÍMICA + ROLES
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS BALANCEADOS", type="primary", use_container_width=True):
    if len(conv_raw) != cupo_total:
        st.error(f"Faltan/Sobran jugadores. Tenés {len(conv_raw)} seleccionados, el formato requiere exactamente {cupo_total}.")
    else:
        convocados = []
        for _, row in conv_raw.iterrows():
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
                "pos_secundaria": str(row["pos_secundaria"]), 
                "rol": str(row["rol"]) if pd.notna(row["rol"]) else "Mixto",
                "valoracion": int(row["valoracion_real"]), 
                "amigo": str(row["amigo"]) if pd.notna(row["amigo"]) else "",
                "ritmo": int(row["ritmo"]),
                "defensa": int(row["defensa"])
            })

        # Funciones de Química y Roles
        def val_eq(e): return sum(x["valoracion"] for x in e)
        def rit_eq(e): return sum(x["ritmo"] for x in e)
        def def_eq(e): return sum(x["defensa"] for x in e)
        def of_eq(e): return sum(1 for x in e if x["rol"] == "Ofensivo")
        def df_eq(e): return sum(1 for x in e if x["rol"] == "Defensivo")
        
        def calcular_costo(e1, e2):
            """Diferencia Global (x3) + Ritmo + Def + Roles Ofensivos (x2) + Roles Defensivos (x2)"""
            diff_val = abs(val_eq(e1) - val_eq(e2)) * 3
            diff_rit = abs(rit_eq(e1) - rit_eq(e2))
            diff_def = abs(def_eq(e1) - def_eq(e2))
            diff_rol_of = abs(of_eq(e1) - of_eq(e2)) * 2
            diff_rol_df = abs(df_eq(e1) - df_eq(e2)) * 2
            return diff_val + diff_rit + diff_def + diff_rol_of + diff_rol_df

        # --- 4.1 EL COMODÍN ---
        if cupo_total == 10: minimos = {"ARQ": 2, "DEF": 0, "MED": 0, "DEL": 0}
        else: minimos = {"ARQ": 2, "DEF": 4, "MED": 4, "DEL": 2}

        cambios_tacticos = []
        for pos_req, min_req in minimos.items():
            cant_actual = sum(1 for j in convocados if j["posicion"] == pos_req)
            faltantes = min_req - cant_actual
            if faltantes > 0:
                candidatos = [j for j in convocados if j["pos_secundaria"] == pos_req and j["posicion"] != pos_req]
                for cand in candidatos:
                    if faltantes == 0: break
                    pos_orig = cand["posicion"]
                    if sum(1 for j in convocados if j["posicion"] == pos_orig) > minimos.get(pos_orig, 0):
                        cand["posicion"] = pos_req
                        cand["pos_secundaria"] = "Ninguna"
                        faltantes -= 1
                        cambios_tacticos.append(f"🔄 **{cand['nombre']}** pasó de {pos_orig} a {pos_req}.")

        if cambios_tacticos:
            with st.expander("🛠️ Ajustes Tácticos Automáticos", expanded=True):
                st.info("El sistema reubicó jugadores polifuncionales:")
                for cambio in cambios_tacticos: st.write(cambio)

        # --- 4.2 AGRUPAR AMIGOS ---
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
        
        # --- 4.3 REPARTO DE ARQUEROS ---
        arqs_g = [g for g in grupos if any(x["posicion"] == "ARQ" for x in g)]
        arqs_g = sorted(arqs_g, key=lambda g: max(x["valoracion"] for x in g if x["posicion"]=="ARQ"), reverse=True)
        if len(arqs_g) >= 2:
            eq1.extend(arqs_g[0]); eq2.extend(arqs_g[1])
            grupos = [g for g in grupos if g not in arqs_g]
        elif len(arqs_g) == 1:
            eq1.extend(arqs_g[0]); grupos.remove(arqs_g[0])
            libres = [g for g in grupos if not any(x["posicion"] == "ARQ" for x in g)]
            if libres:
                m_def = max(libres, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
                eq2.extend(m_def); grupos.remove(m_def)

        # --- 4.4 REGLA FÚTBOL 5 ---
        solos = [g[0] for g in grupos if len(g) == 1 and g[0] not in eq1 and g[0] not in eq2]
        if cupo_total == 10:
            max_arq_1 = max([x["valoracion"] for x in eq1 if x["posicion"] == "ARQ"], default=-1)
            max_arq_2 = max([x["valoracion"] for x in eq2 if x["posicion"] == "ARQ"], default=-1)
            dels_solos = sorted([j for j in solos if j["posicion"] == "DEL"], key=lambda x: x["valoracion"], reverse=True)
            if dels_solos and (max_arq_1 > -1 or max_arq_2 > -1):
                mejor_del = dels_solos[0]
                if max_arq_1 > max_arq_2: eq2.append(mejor_del)
                else: eq1.append(mejor_del)
                solos.remove(mejor_del)

        # --- 4.5 REPARTO DE AMIGOS ---
        g_amigos = sorted([g for g in grupos if len(g) > 1], key=lambda x: sum(j["valoracion"] for j in x), reverse=True)
        for g in g_amigos:
            if val_eq(eq1) <= val_eq(eq2) and len(eq1) + len(g) <= limite_eq: eq1.extend(g)
            else: eq2.extend(g)

        # --- 4.6 REPARTO FLEXIBLE ---
        solos_ordenados = sorted(solos, key=lambda x: x["valoracion"], reverse=True)
        for j in solos_ordenados:
            pos = j["posicion"]
            c1 = sum(1 for x in eq1 if x["posicion"] == pos)
            c2 = sum(1 for x in eq2 if x["posicion"] == pos)
            
            equipo_ideal = 1 if val_eq(eq1) <= val_eq(eq2) else 2
            
            if equipo_ideal == 1:
                if (c1 + 1) - c2 >= 2 and len(eq2) < limite_eq: eq2.append(j)
                elif len(eq1) < limite_eq: eq1.append(j)
                else: eq2.append(j)
            else:
                if (c2 + 1) - c1 >= 2 and len(eq1) < limite_eq: eq1.append(j)
                elif len(eq2) < limite_eq: eq2.append(j)
                else: eq1.append(j)

        # --- 4.7 POST-OPTIMIZACIÓN FINA (Ahora incluye roles) ---
        nombres_amigos = set(j["nombre"] for g in g_amigos for j in g)
        mejoro = True
        while mejoro:
            mejoro = False
            costo_actual = calcular_costo(eq1, eq2)
            
            for j1 in [x for x in eq1 if x["nombre"] not in nombres_amigos and x["posicion"] != "ARQ"]:
                for j2 in [x for x in eq2 if x["nombre"] not in nombres_amigos and x["posicion"] != "ARQ"]:
                    if j1["posicion"] == j2["posicion"]:
                        eq1_sim = [x for x in eq1 if x != j1] + [j2]
                        eq2_sim = [x for x in eq2 if x != j2] + [j1]
                        nuevo_costo = calcular_costo(eq1_sim, eq2_sim)
                        
                        if nuevo_costo < costo_actual:
                            eq1.remove(j1); eq1.append(j2)
                            eq2.remove(j2); eq2.append(j1)
                            costo_actual = nuevo_costo
                            mejoro = True
                            break
                if mejoro: break

        prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
        eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

        prom_v1 = val_eq(eq1) / len(eq1) if eq1 else 0
        prom_r1 = rit_eq(eq1) / len(eq1) if eq1 else 0
        prom_d1 = def_eq(eq1) / len(eq1) if eq1 else 0
        
        prom_v2 = val_eq(eq2) / len(eq2) if eq2 else 0
        prom_r2 = rit_eq(eq2) / len(eq2) if eq2 else 0
        prom_d2 = def_eq(eq2) / len(eq2) if eq2 else 0

        # --- MOSTRAR RESULTADOS ---
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🔵 EQ 1 (Media: {prom_v1:.0f} | Rit: {prom_r1:.0f} | Def: {prom_d1:.0f})")
            st.plotly_chart(dibujar_cancha(eq1, "Balanceado ✅", "#3498db"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq1:
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    rol_txt = f" [{j['rol'][:3]}]" if j['rol'] != "Mixto" else "" # Mostrará [Ofe] o [Def]
                    st.write(f"**{j['posicion']}** - {j['nombre']} {rol_txt}{sec}")
        with col2:
            st.warning(f"🟠 EQ 2 (Media: {prom_v2:.0f} | Rit: {prom_r2:.0f} | Def: {prom_d2:.0f})")
            st.plotly_chart(dibujar_cancha(eq2, "Balanceado ✅", "#e67e22"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq2:
                    sec = f" (Sec: {j['pos_secundaria']})" if j['pos_secundaria'] != "Ninguna" else ""
                    rol_txt = f" [{j['rol'][:3]}]" if j['rol'] != "Mixto" else ""
                    st.write(f"**{j['posicion']}** - {j['nombre']} {rol_txt}{sec}")