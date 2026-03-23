import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border: 1px solid #e9ecef;
    }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def cargar_datos():
    xl = pd.read_excel("Analisis.xlsx", sheet_name=None)
    ventas = xl["Ventas"].copy()
    zonas = xl["Zonas"].copy()
    clientes = xl["Clientes"].copy()

    ventas["FechaVenta"] = pd.to_datetime(ventas["FechaVenta"])
    ventas["Año"] = ventas["FechaVenta"].dt.year
    ventas["Mes"] = ventas["FechaVenta"].dt.month
    ventas["NombreMes"] = ventas["FechaVenta"].dt.strftime("%b")
    ventas["Trimestre"] = "Q" + ventas["FechaVenta"].dt.quarter.astype(str)

    zonas = zonas.rename(columns={"ID_zona": "ID_Zona"})
    df = ventas.merge(zonas, on="ID_Zona").merge(
        clientes[["ID_Cliente", "Nombre", "Clasificacion_credito"]], on="ID_Cliente"
    )
    return df, clientes


df_full, clientes_df = cargar_datos()

# ── SIDEBAR FILTROS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filtros")

    años = sorted(df_full["Año"].unique())
    años_sel = st.multiselect("Año", años, default=[y for y in años if y in [2016, 2017, 2018]])

    zonas_lista = sorted(df_full["Zona"].unique())
    zonas_sel = st.multiselect("Zona", zonas_lista, default=zonas_lista)

    clientes_lista = sorted(df_full["Nombre"].unique())
    clientes_sel = st.multiselect("Cliente", clientes_lista, default=clientes_lista)

    credito_lista = sorted(df_full["Clasificacion_credito"].unique())
    credito_sel = st.multiselect("Clasificación crédito", credito_lista, default=credito_lista)

    st.divider()
    st.caption("Los filtros aplican a todos los gráficos")

# ── FILTRAR ──────────────────────────────────────────────────────────────────
df = df_full[
    df_full["Año"].isin(años_sel) &
    df_full["Zona"].isin(zonas_sel) &
    df_full["Nombre"].isin(clientes_sel) &
    df_full["Clasificacion_credito"].isin(credito_sel)
]

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("📊 Dashboard de Ventas")
st.caption(f"Mostrando {len(df):,} transacciones · {df['Año'].min() if len(df) else '-'} – {df['Año'].max() if len(df) else '-'}")

# ── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total = df["Venta"].sum()
ticket_prom = df["Venta"].mean()
transacciones = len(df)
clientes_activos = df["ID_Cliente"].nunique()
vendedores = df["ID_Vendedor"].nunique()

k1.metric("Ventas totales", f"${total/1e9:.2f}B")
k2.metric("Ticket promedio", f"${ticket_prom/1e6:.2f}M")
k3.metric("Transacciones", f"{transacciones:,}")
k4.metric("Clientes activos", clientes_activos)
k5.metric("Vendedores", vendedores)

st.divider()

# ── FILA 1: Ventas anuales + trimestrales ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Ventas anuales")
    anuales = df.groupby("Año")["Venta"].sum().reset_index()
    anuales["VentaM"] = anuales["Venta"] / 1e6
    anuales["YoY"] = anuales["VentaM"].pct_change() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=anuales["Año"], y=anuales["VentaM"],
        name="Ventas ($M)", marker_color="#378ADD", text=anuales["VentaM"].round(0).astype(int),
        texttemplate="$%{text}M", textposition="outside"
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=anuales["Año"], y=anuales["YoY"],
        name="Crecimiento YoY %", mode="lines+markers",
        line=dict(color="#E24B4A", width=2), marker=dict(size=7)
    ), secondary_y=True)
    fig.update_layout(height=320, margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.15))
    fig.update_yaxes(title_text="Ventas ($M)", secondary_y=False)
    fig.update_yaxes(title_text="YoY %", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Ventas trimestrales por año")
    trim = df.groupby(["Año", "Trimestre"])["Venta"].sum().reset_index()
    trim["VentaM"] = trim["Venta"] / 1e6
    fig2 = px.bar(trim, x="Trimestre", y="VentaM", color="Año",
                  barmode="group", color_discrete_sequence=["#378ADD", "#1D9E75", "#EF9F27", "#E24B4A"],
                  labels={"VentaM": "Ventas ($M)", "Trimestre": ""})
    fig2.update_layout(height=320, margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig2, use_container_width=True)

# ── FILA 2: Zona + Mensual ───────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Ventas por zona")
    por_zona = df.groupby("Zona")["Venta"].sum().reset_index()
    por_zona["VentaM"] = por_zona["Venta"] / 1e6
    fig3 = px.pie(por_zona, values="VentaM", names="Zona", hole=0.4,
                  color_discrete_sequence=["#378ADD", "#1D9E75", "#EF9F27", "#E24B4A"])
    fig3.update_traces(textinfo="label+percent", textposition="outside")
    fig3.update_layout(height=320, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Estacionalidad mensual")
    MESES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
             7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    mensual = df.groupby("Mes")["Venta"].sum().reset_index()
    mensual["VentaM"] = mensual["Venta"] / 1e6
    mensual["MesNombre"] = mensual["Mes"].map(MESES)
    max_mes = mensual["VentaM"].max()
    mensual["Color"] = mensual["VentaM"].apply(
        lambda v: "#E24B4A" if v == max_mes else ("#EF9F27" if v < mensual["VentaM"].quantile(0.3) else "#378ADD")
    )
    fig4 = px.bar(mensual, x="MesNombre", y="VentaM",
                  color="Color", color_discrete_map="identity",
                  labels={"VentaM": "Ventas ($M)", "MesNombre": ""})
    fig4.update_layout(height=320, margin=dict(t=20, b=20), showlegend=False)
    fig4.update_xaxes(tickangle=0)
    st.plotly_chart(fig4, use_container_width=True)

# ── FILA 3: Zona × Año (líneas) ──────────────────────────────────────────────
st.subheader("Evolución por zona y año")
zona_año = df.groupby(["Zona", "Año"])["Venta"].sum().reset_index()
zona_año["VentaM"] = zona_año["Venta"] / 1e6
fig5 = px.line(zona_año, x="Año", y="VentaM", color="Zona", markers=True,
               color_discrete_sequence=["#378ADD", "#1D9E75", "#EF9F27", "#E24B4A"],
               labels={"VentaM": "Ventas ($M)", "Año": ""})
fig5.update_layout(height=280, margin=dict(t=20, b=20))
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── FILA 4: Clientes + Vendedores ────────────────────────────────────────────
col5, col6 = st.columns([3, 2])

with col5:
    st.subheader("Ranking de clientes")
    rank = df.groupby("Nombre").agg(
        Total=("Venta", "sum"),
        Transacciones=("Venta", "count"),
        Promedio=("Venta", "mean")
    ).reset_index().sort_values("Total", ascending=False)
    rank = rank.merge(clientes_df[["Nombre", "Clasificacion_credito"]], on="Nombre", how="left")
    rank["Total ($M)"] = (rank["Total"] / 1e6).round(1)
    rank["Promedio ($M)"] = (rank["Promedio"] / 1e6).round(2)
    rank = rank[["Nombre", "Total ($M)", "Transacciones", "Promedio ($M)", "Clasificacion_credito"]]
    rank.columns = ["Cliente", "Total ($M)", "Transac.", "Promedio ($M)", "Crédito"]
    st.dataframe(rank.reset_index(drop=True), use_container_width=True, hide_index=True)

with col6:
    st.subheader("Top 10 vendedores")
    top_v = df.groupby("ID_Vendedor")["Venta"].sum().sort_values(ascending=False).head(10).reset_index()
    top_v["VentaM"] = top_v["Venta"] / 1e6
    top_v["Vendedor"] = "V" + top_v["ID_Vendedor"].astype(str)
    fig6 = px.bar(top_v, x="VentaM", y="Vendedor", orientation="h",
                  color_discrete_sequence=["#378ADD"],
                  labels={"VentaM": "Ventas ($M)", "Vendedor": ""})
    fig6.update_layout(height=340, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig6, use_container_width=True)

# ── FILA 5: Producto + Crédito ───────────────────────────────────────────────
col7, col8 = st.columns(2)

with col7:
    st.subheader("Ventas por producto")
    prod = df.groupby("ID_producto")["Venta"].sum().reset_index()
    prod["VentaM"] = prod["Venta"] / 1e6
    prod["Producto"] = "Producto " + prod["ID_producto"].astype(str)
    prod = prod.sort_values("VentaM", ascending=False)
    fig7 = px.bar(prod, x="Producto", y="VentaM",
                  color_discrete_sequence=["#7F77DD"],
                  labels={"VentaM": "Ventas ($M)", "Producto": ""})
    fig7.update_layout(height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.subheader("Ventas por clasificación de crédito")
    cred = df.groupby("Clasificacion_credito")["Venta"].sum().reset_index()
    cred["VentaM"] = cred["Venta"] / 1e6
    cred = cred.sort_values("VentaM", ascending=False)
    CRED_COLORS = {"AA":"#1D9E75","A":"#5DCAA5","B":"#378ADD","BB":"#EF9F27","C":"#E24B4A","CC":"#A32D2D"}
    fig8 = px.bar(cred, x="Clasificacion_credito", y="VentaM",
                  color="Clasificacion_credito", color_discrete_map=CRED_COLORS,
                  labels={"VentaM": "Ventas ($M)", "Clasificacion_credito": "Clasificación"})
    fig8.update_layout(height=300, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig8, use_container_width=True)

st.divider()
st.caption("Dashboard generado por Javier Sotelo con Streamlit + Plotly · Datos: Analisis.xlsx")

#streamlit run "C:/Users/estud/PROYECTOS Py/Dashboard Streamlit/app.py"
