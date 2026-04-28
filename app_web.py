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

    #Coordenadas verticales fijas para las líneas
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
    
    #Estilo de la cancha
    fig.update_layout(
        title=dict(text=titulo, font=dict(color='white', size=18), x=0.5),
        width=350, height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 110], showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#234721", 
        paper_bgcolor="#1e1e1e", 
    )

    #lineas de arco y area
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
with st.expander("➕ Gestionar Plantel (Agregar Jugador)"):
    with st.form("form_nuevo"):
        c1, c2, c3, c4 = st.columns(4)
        nombre_nuevo = c1.text_input("Nombre")
        pos_nuevo = c2.selectbox("Posición", ["ARQ", "DEF", "MED", "DEL"])
        val_nuevo = c3.number_input("Valoración", min_value=1, max_value=99, value=80)
        amigo_nuevo = c4.text_input("Dúo / Amigo (opcional)")
        
        if st.form_submit_button("Guardar en Base de Datos"):
            if nombre_nuevo:
                conn = conectar_db()
                conn.execute("INSERT INTO jugadores (nombre, posicion, valoracion, amigo) VALUES (?, ?, ?, ?)", 
                             (nombre_nuevo, pos_nuevo, val_nuevo, amigo_nuevo))
                conn.commit()
                conn.close()
                st.success(f"¡{nombre_nuevo} agregado! Recargá la página.")
                st.rerun()

# Lectura y edición de la tabla
conn = conectar_db()
df = pd.read_sql("SELECT nombre, posicion, valoracion, amigo FROM jugadores ORDER BY nombre COLLATE NOCASE ASC", conn)
conn.close()

df.insert(0, "Selección", False)

st.subheader("Lista de Jugadores")
tabla_editada = st.data_editor(
    df,
    column_config={
        "Selección": st.column_config.CheckboxColumn("¿Juega?", default=False),
        "valoracion": st.column_config.ProgressColumn("Nivel", min_value=0, max_value=99, format="%d")
    },
    disabled=["nombre", "posicion", "valoracion", "amigo"], 
    hide_index=True,
    use_container_width=True
)

convocados_raw = tabla_editada[tabla_editada["Selección"] == True]

# ==========================================
# 4. ALGORITMO DE BALANCEO MEJORADO
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS BALANCEADOS", type="primary", use_container_width=True):
    
    if len(convocados_raw) != 16:
        st.error(f"⚠️ Selección incorrecta: Tenés {len(convocados_raw)} de 16 jugadores necesarios.")
    else:
        # Convertir datos para el algoritmo
        convocados = []
        for _, row in convocados_raw.iterrows():
            amigo_val = str(row["amigo"]) if pd.notna(row["amigo"]) and str(row["amigo"]) != "" else ""
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
                "valoracion": int(row["valoracion"]), 
                "amigo": amigo_val
            })

        # 4.1. Agrupar por Amigos/Dúos
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
        
        # 4.2. Reparto de Arqueros y Compensación
        if len(arqs) == 1:
            st.info("ℹ️ Compensación aplicada: Mejor DEF vs único ARQ.")
            eq1.extend(grupos_con_arq[0])
            if grupos_sin_arq:
                m_def_g = max(grupos_sin_arq, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
                eq2.extend(m_def_g)
                grupos_sin_arq.remove(m_def_g)
            grupos_restantes = grupos_sin_arq
        elif len(arqs) == 2:
            st.info("ℹ️ Un arquero asignado a cada equipo.")
            if len(grupos_con_arq) >= 2:
                eq1.extend(grupos_con_arq[0])
                eq2.extend(grupos_con_arq[1])
                grupos_restantes = grupos_sin_arq
            else:
                eq1.extend(grupos_con_arq[0]) # Van juntos si se marcaron como amigos
                grupos_restantes = grupos_sin_arq
        else:
            grupos_restantes = grupos_sin_arq + grupos_con_arq

        # 4.3. Reparto de Bloques (Amigos)
        grupos_amigos = [g for g in grupos_restantes if len(g) > 1]
        grupos_solos = [g for g in grupos_restantes if len(g) == 1]

        def val_eq(e): return sum(x["valoracion"] for x in e)

        grupos_amigos.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
        for g in grupos_amigos:
            if len(eq1) + len(g) <= 8 and (val_eq(eq1) <= val_eq(eq2) or len(eq2) == 8):
                eq1.extend(g)
            else: eq2.extend(g)

        # 4.4. Reparto Línea por Línea (Evita amontonar posiciones)
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

        # Orden final táctico para visualización
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
                for j in eq1: st.write(f"**{j['posicion']}** - {j['nombre']} ({j['valoracion']})")

        with col2:
            prom2 = val_eq(eq2)/8 if len(eq2)==8 else 0
            st.warning("🟠 EQUIPO 2")
            st.plotly_chart(dibujar_cancha(eq2, f"Promedio: {prom2:.2f}", "#e67e22"), use_container_width=True)
            with st.expander("Lista Detallada"):
                for j in eq2: st.write(f"**{j['posicion']}** - {j['nombre']} ({j['valoracion']})")