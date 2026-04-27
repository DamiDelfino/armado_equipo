import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go # <-- Acá está la nueva librería para la cancha

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS
# ==========================================
def conectar_db():
    return sqlite3.connect("futbol_plantel.db")

# ==========================================
# 2. FUNCIONES DE DIBUJO (PLOTLY)
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
        x=coords_x, y=coords_y,
        mode='markers+text',
        text=nombres,
        textposition="top center",
        marker=dict(size=25, color=color_puntos, line=dict(width=2, color='white')),
        textfont=dict(color='white', size=12)
    ))

    fig.update_layout(
        title=dict(text=titulo, font=dict(color='white', size=18), x=0.5),
        width=350, height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 110], showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#234721", 
        paper_bgcolor="#1e1e1e", 
    )

    fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=15, line=dict(color="white")) 
    fig.add_shape(type="circle", x0=40, y0=95, x1=60, y1=105, line=dict(color="white")) 
    
    return fig

# ==========================================
# 3. CONFIGURACIÓN DE LA PÁGINA WEB
# ==========================================
st.set_page_config(page_title="Fútbol 8 App", page_icon="⚽", layout="wide")

st.title("⚽ Armador de Equipos Equitativos")
st.markdown("Seleccioná a los 16 jugadores que vinieron hoy y el sistema armará los equipos.")

# ==========================================
# 4. FORMULARIO PARA AGREGAR JUGADORES
# ==========================================
with st.expander("➕ Agregar nuevo jugador a la base de datos"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4 = st.columns(4)
        nombre_nuevo = c1.text_input("Nombre")
        pos_nuevo = c2.selectbox("Pos", ["ARQ", "DEF", "MED", "DEL"])
        val_nuevo = c3.number_input("Val", min_value=1, max_value=99, value=80)
        amigo_nuevo = c4.text_input("Dúo/Amigo")
        
        btn_guardar = st.form_submit_button("Guardar en BD")
        if btn_guardar and nombre_nuevo:
            conn = conectar_db()
            conn.execute("INSERT INTO jugadores (nombre, posicion, valoracion, amigo) VALUES (?, ?, ?, ?)", 
                         (nombre_nuevo, pos_nuevo, val_nuevo, amigo_nuevo))
            conn.commit()
            conn.close()
            st.success("¡Jugador guardado! Recargá la página para verlo.")
            st.rerun()

# ==========================================
# 5. TABLA INTERACTIVA (SELECCIÓN)
# ==========================================
conn = conectar_db()
df = pd.read_sql("SELECT nombre, posicion, valoracion, amigo FROM jugadores ORDER BY nombre COLLATE NOCASE ASC", conn)
conn.close()

df.insert(0, "Juega Hoy", False)

st.subheader("Plantel Disponible")
tabla_editada = st.data_editor(
    df,
    column_config={
        "Juega Hoy": st.column_config.CheckboxColumn("¿Juega Hoy?", default=False),
        "valoracion": st.column_config.ProgressColumn("Nivel", min_value=0, max_value=99, format="%d")
    },
    disabled=["nombre", "posicion", "valoracion", "amigo"], 
    hide_index=True,
    use_container_width=True
)

seleccionados_df = tabla_editada[tabla_editada["Juega Hoy"] == True]

# ==========================================
# 6. ALGORITMO Y RESULTADOS
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS", type="primary", use_container_width=True):
    
    if len(seleccionados_df) != 16:
        st.error(f"⚠️ Tenés que seleccionar exactamente 16 jugadores. Tildaste: {len(seleccionados_df)}")
    else:
        convocados = []
        for index, row in seleccionados_df.iterrows():
            amigo_val = str(row["amigo"]) if pd.notna(row["amigo"]) and str(row["amigo"]) != "" else ""
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
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
            st.info("ℹ️ Se detectó 1 solo Arquero. El mejor Defensor va al equipo contrario.")
            eq1.extend(grupos_con_arq[0])
            if grupos_sin_arq:
                m_def_g = max(grupos_sin_arq, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
                eq2.extend(m_def_g)
                grupos_sin_arq.remove(m_def_g)
            grupos_restantes = grupos_sin_arq
            
        elif len(arqs) == 2:
            st.info("ℹ️ Se detectaron 2 Arqueros. Se asignará uno a cada equipo.")
            if len(grupos_con_arq) >= 2:
                eq1.extend(grupos_con_arq[0])
                eq2.extend(grupos_con_arq[1])
                grupos_restantes = grupos_sin_arq
            else:
                eq1.extend(grupos_con_arq[0])
                grupos_restantes = grupos_sin_arq
                
        else:
            grupos_restantes = grupos_sin_arq + grupos_con_arq

        grupos_restantes.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
        
        for g in grupos_restantes:
            if len(eq1) + len(g) <= 8 and (sum(x["valoracion"] for x in eq1) <= sum(x["valoracion"] for x in eq2) or len(eq2) == 8):
                eq1.extend(g)
            else: 
                eq2.extend(g)

        prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
        eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))

        # --- DIBUJADO DE LA CANCHA Y RESULTADOS ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            prom1 = sum(x["valoracion"] for x in eq1)/8 if len(eq1) == 8 else 0
            st.success(f"🔵 EQUIPO 1")
            fig1 = dibujar_cancha(eq1, f"Promedio: {prom1:.2f}", "#3498db")
            st.plotly_chart(fig1, use_container_width=True)
            
            with st.expander("Ver lista de jugadores"):
                for j in eq1:
                    amigo_txt = f" *(con {j['amigo']})*" if j['amigo'] else ""
                    st.caption(f"**{j['posicion']}** | {j['nombre']} {amigo_txt}")

        with col2:
            prom2 = sum(x["valoracion"] for x in eq2)/8 if len(eq2) == 8 else 0
            st.warning(f"🟠 EQUIPO 2")
            fig2 = dibujar_cancha(eq2, f"Promedio: {prom2:.2f}", "#e67e22")
            st.plotly_chart(fig2, use_container_width=True)
            
            with st.expander("Ver lista de jugadores"):
                for j in eq2:
                    amigo_txt = f" *(con {j['amigo']})*" if j['amigo'] else ""
                    st.caption(f"**{j['posicion']}** | {j['nombre']} {amigo_txt}")