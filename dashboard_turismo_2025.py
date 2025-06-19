import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Camping Nerpio")
st.title("Dashboard de Análisis - Camping Nerpio 2025")

@st.cache_data
def cargar_datos():
    df_reservas = pd.read_excel("ESTADISTICA RESERVAS WEB EN 2025.xlsx", sheet_name=None)
    df_nacionalidades = pd.read_excel("ESTADISTICA NACIONALIDADES 25.xlsx", sheet_name=None)
    df_edades = pd.read_excel("ESTADISTICA SOBRE EDADES Y ALOJAMIENTOS 2025 (1).xlsx", sheet_name=None)
    return df_reservas, df_nacionalidades, df_edades

df_reservas, df_nacionalidades, df_edades = cargar_datos()

st.sidebar.title("Filtros")
seccion = st.sidebar.radio("Ir a sección:", ["Resumen general", "Reservas mensuales", "Nacionalidades", "Edad por alojamiento"])

# --------- RESUMEN GENERAL ---------
if seccion == "Resumen general":
    st.subheader("Perfil general del cliente")
    st.markdown("- Principalmente **español**, de entre **41 y 50 años**.")
    st.markdown("- Alojamiento más usado: **Parcela**.")
    st.markdown("- Mes de mayor actividad: **abril y mayo**.")
    st.caption("Este perfil permite adaptar la oferta a las necesidades de un público familiar y nacional.")

# --------- RESERVAS MENSUALES ---------
elif seccion == "Reservas mensuales":
    import re
    def extraer_bloques_estancia_robusto(df_hoja):
        bloques = []
        i = 0
        while i < len(df_hoja):
            fila = df_hoja.iloc[i]
            texto = " ".join([str(x) for x in fila if isinstance(x, str)])
            if "FECHAS DE ESTANCIA" in texto:
                match = re.search(r"\((\d{2}/\d{2}/\d{2}) AL (\d{2}/\d{2}/\d{2})\)", texto)
                if not match:
                    i += 1
                    continue
                fecha_inicio = match.group(1)
                mes = pd.to_datetime(fecha_inicio, format="%d/%m/%y").strftime("%Y-%m")
                i += 3
                while i < len(df_hoja):
                    fila = df_hoja.iloc[i]
                    if isinstance(fila[0], str) and fila[0].strip().upper() == "TOTALES":
                        break
                    if not fila.isnull().all():
                        alojamiento = fila[1]
                        cantidad = fila[2]
                        if pd.notna(alojamiento):
                            bloques.append({"Mes": mes, "Alojamiento": alojamiento, "Cantidad": pd.to_numeric(cantidad, errors='coerce')})
                    i += 1
            else:
                i += 1
        return bloques

    registros = []
    for hoja in df_reservas.values():
        registros.extend(extraer_bloques_estancia_robusto(hoja))

    df = pd.DataFrame(registros)
    top_alojamientos = df.groupby("Alojamiento")["Cantidad"].sum().nlargest(5).index

    st.subheader("Evolución mensual de reservas por alojamiento")
    colores = px.colors.qualitative.Set1
    explicaciones = {
        "Casa Rural 4 Pax": "Este alojamiento presenta su pico más alto en mayo, lo que indica que es popular en primavera. Ideal para escapadas familiares o puentes largos.",
        "Parcela": "Las parcelas muestran un crecimiento constante hacia los meses de verano, especialmente agosto. Indica una alta demanda de campistas estacionales.",
        "Parcela Grande Caravana o Tienda": "Tiene un aumento muy claro entre marzo y abril, lo que sugiere su atractivo para escapadas de primavera o Semana Santa.",
        "MH - 6 Pax": "Su ocupación aumenta significativamente entre mayo y julio, lo cual refleja una preferencia para grupos más grandes o familias en temporada alta.",
        "Casas Alpinas": "A pesar de tener una demanda estable, los picos en abril y julio indican que se trata de un alojamiento de nicho buscado en épocas específicas."
    }

    for i, alojamiento in enumerate(top_alojamientos):
        df_aux = df[df["Alojamiento"] == alojamiento]
        fig = px.bar(df_aux, x="Mes", y="Cantidad", title=alojamiento,
                     color_discrete_sequence=[colores[i % len(colores)]])
        st.plotly_chart(fig, use_container_width=True)
        st.caption(explicaciones.get(alojamiento, "Destaca por su alta demanda en mayo y verano, ideal para familias numerosas, aunque marzo y abril muestran margen de mejora.."))

    st.markdown("---")
    st.subheader("Conclusión general")
    st.markdown(
        "Los cinco alojamientos principales muestran patrones de estacionalidad distintos, siendo mayo y agosto los meses más intensos en reservas. "
        "Las parcelas destacan en verano, mientras que las casas rurales y alpinas se prefieren en primavera. "
        "Esto permite afinar estrategias de promoción por tipo de alojamiento y estación del año."
    )

# --------- NACIONALIDADES ---------
elif seccion == "Nacionalidades":
    registros = []
    for mes, hoja in df_nacionalidades.items():
        hoja = hoja.dropna(how="all")
        hoja.columns = hoja.iloc[0]
        hoja = hoja[1:]
        hoja = hoja.set_index(hoja.columns[0])
        hoja = hoja[~hoja.index.str.upper().str.contains("TOTAL")]
        hoja_total = hoja.iloc[:, -3:].copy()
        hoja_total.columns = ["LLEGADA", "PERNOCT", "EMPLAZA"]
        hoja_total["NACIONALIDAD"] = hoja_total.index
        for col in ["LLEGADA", "PERNOCT", "EMPLAZA"]:
            hoja_total[col] = pd.to_numeric(hoja_total[col], errors="coerce")
        registros.append(hoja_total.reset_index(drop=True))

    df_completo = pd.concat(registros, ignore_index=True)
    mapa = df_completo.groupby("NACIONALIDAD")["LLEGADA"].sum().reset_index()
    mapa.columns = ["country", "visitors"]

    traduccion_paises = {
        "España": "Spain",
        "Francia": "France",
        "Alemania": "Germany",
        "Rumania": "Romania",
        "Bélgica": "Belgium",
        "Argentina": "Argentina",
        "México": "Mexico",
        "Suiza": "Switzerland",
        "Suecia": "Sweden",
        "Austria": "Austria",
        "Noruega": "Norway",
        "Nueva Zelanda": "New Zealand",
        "Bosnia": "Bosnia and Herzegovina",
        "Resto de África": None,
        "Otros paises": None
    }

    mapa["country"] = mapa["country"].replace(traduccion_paises)
    mapa = mapa.dropna(subset=["country"])
    import numpy as np

    mapa["visitors_log"] = mapa["visitors"].apply(lambda x: np.log10(x + 1))

    fig = px.choropleth(
        mapa,
        locations="country",
        locationmode="country names",
        scope="europe",
        color="visitors_log",
        hover_name="country",
        hover_data={"visitors": True, "visitors_log": False},
        color_continuous_scale="Plasma",
        title="Visitantes por país (Europa)",
    )

    fig.update_layout(coloraxis_colorbar=dict(
        title="Escala log. de visitantes",
        tickvals=[0, 1, 2, 3],
        ticktext=["1", "10", "100", "1000+"]
    ))

    st.plotly_chart(fig, use_container_width=True)

    st.caption("El mapa representa el volumen total de llegadas desde distintos países europeos durante el periodo analizado.")

# --------- EDAD POR ALOJAMIENTO ---------
elif seccion == "Edad por alojamiento":
    registros_normalizados = []
    for alojamiento, df in df_edades.items():
        df = df.dropna(how="all").reset_index(drop=True)
        tramos = df.iloc[1, 1:].tolist()
        datos = df.iloc[2:, 1:len(tramos)+1]
        datos.columns = tramos
        datos = datos.apply(pd.to_numeric, errors="coerce").fillna(0)
        totales = datos.sum()
        for tramo, valor in totales.items():
            registros_normalizados.append({
                "ALOJAMIENTO": alojamiento,
                "TRAMO_EDAD": tramo,
                "CANTIDAD": valor
            })

    df_edades_normalizado = pd.DataFrame(registros_normalizados)
    st.subheader("Distribución de edad por alojamiento")
    fig = px.bar(
        df_edades_normalizado, x="ALOJAMIENTO", y="CANTIDAD",
        color="TRAMO_EDAD", title="Clientes por tramo de edad y alojamiento",
        barmode="stack", labels={"CANTIDAD": "Clientes", "TRAMO_EDAD": "Edad"}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Este gráfico muestra qué edades se concentran más en cada tipo de alojamiento. Ayuda a perfilar mejor las preferencias de cada grupo.")
