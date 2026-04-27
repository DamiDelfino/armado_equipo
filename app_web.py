import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS
# ==========================================
def conectar_db():
    return sqlite3.connect("futbol_plantel.db")

# ==========================================
# 2. CONFIGURACIÓN DE LA PÁGINA WEB
# ==========================================
# Esto configura la pestaña del navegador
st.set_page_config(page_title="Fútbol 8 App", page_icon="⚽", layout="centered")

st.title("⚽ Armador de Equipos Equitativos")
st.markdown("Seleccioná a los 16 jugadores que vinieron hoy y el sistema armará los equipos.")

# ==========================================
# 3. FORMULARIO PARA AGREGAR JUGADORES
# ==========================================
# Usamos un "expander" (un acordeón que se despliega) para no ocupar tanta pantalla
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
            st.rerun() # Esto refresca la página automáticamente

# ==========================================
# 4. TABLA INTERACTIVA (SELECCIÓN)
# ==========================================
conn = conectar_db()
# Pandas lee la base de datos y la convierte en una tabla fácil de usar
df = pd.read_sql("SELECT nombre, posicion, valoracion, amigo FROM jugadores ORDER BY nombre COLLATE NOCASE ASC", conn)
conn.close()

# Le agregamos una columna falsa al principio con valor False (cajas destildadas)
df.insert(0, "Juega Hoy", False)

# Mostramos la tabla interactiva en la web
st.subheader("Plantel Disponible")
tabla_editada = st.data_editor(
    df,
    column_config={
        "Juega Hoy": st.column_config.CheckboxColumn("¿Juega Hoy?", default=False),
        "valoracion": st.column_config.ProgressColumn("Nivel", min_value=0, max_value=99, format="%d")
    },
    disabled=["nombre", "posicion", "valoracion", "amigo"], # Bloqueamos para que solo puedan tildar
    hide_index=True,
    use_container_width=True
)

# Filtramos solo los que el usuario tildó
seleccionados_df = tabla_editada[tabla_editada["Juega Hoy"] == True]

# ==========================================
# 5. ALGORITMO Y RESULTADOS
# ==========================================
if st.button("⚖️ GENERAR EQUIPOS", type="primary", use_container_width=True):
    
    if len(seleccionados_df) != 16:
        st.error(f"⚠️ Tenés que seleccionar exactamente 16 jugadores. Tildaste: {len(seleccionados_df)}")
    else:
        # Convertimos la tabla de pandas de nuevo a nuestra lista de diccionarios
        convocados = []
        for index, row in seleccionados_df.iterrows():
            amigo_val = str(row["amigo"]) if pd.notna(row["amigo"]) and str(row["amigo"]) != "" else ""
            convocados.append({
                "nombre": str(row["nombre"]), 
                "posicion": str(row["posicion"]), 
                "valoracion": int(row["valoracion"]), 
                "amigo": amigo_val
            })

       # --- INICIO DEL ALGORITMO ---
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
        
        # 1. Separamos los grupos con arqueros de los grupos sin arqueros
        grupos_con_arq = [g for g in grupos if any(x["posicion"] == "ARQ" for x in g)]
        grupos_sin_arq = [g for g in grupos if not any(x["posicion"] == "ARQ" for x in g)]
        
        # REGLA 1: Solo 1 Arquero (Compensación con Defensor)
        if len(arqs) == 1:
            st.info("ℹ️ Se detectó 1 solo Arquero. El mejor Defensor va al equipo contrario.")
            eq1.extend(grupos_con_arq[0])
            if grupos_sin_arq:
                m_def_g = max(grupos_sin_arq, key=lambda g: max((x["valoracion"] for x in g if x["posicion"]=="DEF"), default=-1))
                eq2.extend(m_def_g)
                grupos_sin_arq.remove(m_def_g)
            grupos_restantes = grupos_sin_arq
            
        # REGLA 2: Exactamente 2 Arqueros (Reparto Equitativo Obligatorio)
        elif len(arqs) == 2:
            st.info("ℹ️ Se detectaron 2 Arqueros. Se asignará uno a cada equipo.")
            if len(grupos_con_arq) >= 2:
                # Mandamos obligatoriamente un arquero a cada equipo
                eq1.extend(grupos_con_arq[0])
                eq2.extend(grupos_con_arq[1])
                grupos_restantes = grupos_sin_arq
            else:
                # Caso extremo: los dos arqueros se marcaron como "amigos" entre sí. Van juntos.
                eq1.extend(grupos_con_arq[0])
                grupos_restantes = grupos_sin_arq
                
        # REGLA 3: Cero Arqueros
        else:
            grupos_restantes = grupos_sin_arq + grupos_con_arq

        # Repartimos el resto de los grupos para nivelar los promedios
        grupos_restantes.sort(key=lambda g: sum(x["valoracion"] for x in g), reverse=True)
        
        for g in grupos_restantes:
            # Validamos que el equipo no se pase de 8 integrantes
            if len(eq1) + len(g) <= 8 and (sum(x["valoracion"] for x in eq1) <= sum(x["valoracion"] for x in eq2) or len(eq2) == 8):
                eq1.extend(g)
            else: 
                eq2.extend(g)

        # Ordenamos visualmente: ARQ, DEF, MED, DEL
        prioridad = {"ARQ": 0, "DEF": 1, "MED": 2, "DEL": 3}
        eq1.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        eq2.sort(key=lambda x: prioridad.get(x["posicion"], 4))
        # --- FIN DEL ALGORITMO ---

        # Mostrar los resultados en dos columnas (Ideal para web/celular)
        st.divider() # Línea separadora
        col1, col2 = st.columns(2)
        
        with col1:
            prom1 = sum(x["valoracion"] for x in eq1)/8
            st.success(f"🔵 EQUIPO 1 (Prom: {prom1:.2f})")
            for j in eq1:
                amigo_txt = f" *(con {j['amigo']})*" if j['amigo'] else ""
                st.markdown(f"**{j['posicion']}** | {j['nombre']} ({j['valoracion']}){amigo_txt}")

        with col2:
            prom2 = sum(x["valoracion"] for x in eq2)/8
            st.warning(f"🟠 EQUIPO 2 (Prom: {prom2:.2f})")
            for j in eq2:
                amigo_txt = f" *(con {j['amigo']})*" if j['amigo'] else ""
                st.markdown(f"**{j['posicion']}** | {j['nombre']} ({j['valoracion']}){amigo_txt}")