import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Função para carregamento dos dados
@st.cache_data
def load_data():
    base_path = os.path.join(os.path.dirname(__file__), 'base_tratada.xlsx')
    resumo_path = os.path.join(os.path.dirname(__file__), 'resumo_ocupacao.xlsx')
    df_base = pd.read_excel(base_path)
    resumo = pd.read_excel(resumo_path)
    return df_base, resumo

# Utilidade para aplicar filtro de unidade
def aplicar_filtro_unidade(df, unidade):
    if unidade != "Todos":
        return df[df["Unidade"] == unidade].copy()
    return df.copy()

# Carrega os dados originais
df_base, resumo = load_data()

# --- Filtro na Sidebar ---
st.sidebar.header("Filtro por Unidade")
unit_options = ["Todos", "Rac Rec", "Rac For"]
unit_filter = st.sidebar.selectbox("Selecione a Unidade", unit_options)

st.markdown("""
<style>
h1 {
    font-size: 33px !important;
}
</style>
""", unsafe_allow_html=True)

# Título do Dashboard
st.title("Dashboard Resumo de Ocupação")

# Exibir o intervalo de datas da base
datas_validas = pd.to_datetime(df_base["Nome Da Origem"], format="%d/%m/%Y", errors="coerce").dropna()
data_min = datas_validas.min()
data_max = datas_validas.max()

if pd.notnull(data_min) and pd.notnull(data_max):
    st.markdown(f"**Período dos dados:** de {data_min.strftime('%d/%m/%Y')} a {data_max.strftime('%d/%m/%Y')}")

st.markdown("""
<style>
h3 {
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)

# --- KPIs (dados do resumo) ---
st.subheader("KPIs de Ocupação")
col1, col2, col3, col4 = st.columns(4)
try:
    overall_rac_rec_basico = resumo[(resumo["Unidade"] == "Rac Rec") & (resumo["Grupo"] == "Básico")]["Ocupação (%)"].values[0]
    overall_rac_rec_especial = resumo[(resumo["Unidade"] == "Rac Rec") & (resumo["Grupo"] == "Especial")]["Ocupação (%)"].values[0]
    overall_rac_for_basico  = resumo[(resumo["Unidade"] == "Rac For") & (resumo["Grupo"] == "Básico")]["Ocupação (%)"].values[0]
    overall_rac_for_especial = resumo[(resumo["Unidade"] == "Rac For") & (resumo["Grupo"] == "Especial")]["Ocupação (%)"].values[0]
except IndexError:
    st.error("Erro ao recuperar KPIs do arquivo resumo.")
    overall_rac_rec_basico = overall_rac_rec_especial = overall_rac_for_basico = overall_rac_for_especial = None

with col1:
    if overall_rac_rec_basico is not None:
        st.metric("Rac Rec - Básico", f"{overall_rac_rec_basico:.2f}%")
with col2:
    if overall_rac_rec_especial is not None:
        st.metric("Rac Rec - Especial", f"{overall_rac_rec_especial:.2f}%")
with col3:
    if overall_rac_for_basico is not None:
        st.metric("Rac For - Básico", f"{overall_rac_for_basico:.2f}%")
with col4:
    if overall_rac_for_especial is not None:
        st.metric("Rac For - Especial", f"{overall_rac_for_especial:.2f}%")

# --- Tabela de Resumo ---
st.subheader("Tabela de Resumo de Ocupação")
colunas_desejadas = ["Unidade", "Grupo", "Ocupação (%)", "Alugados", "Qtd. Total"]
df_tabela = resumo[colunas_desejadas].copy()
df_tabela["Ocupação (%)"] = df_tabela["Ocupação (%)"].map(lambda x: f"{x:.2f}")
st.dataframe(df_tabela)

# --- Gráfico de Linha: Ocupação ao longo do tempo ---
st.subheader("Evolução da Ocupação")
df_linha = aplicar_filtro_unidade(df_base, unit_filter)
df_linha = df_linha[df_linha["Status"].isin(["Alugado", "Disponível"])]
df_linha["Data"] = pd.to_datetime(df_linha["Nome Da Origem"], format='%d/%m/%Y', errors='coerce')
df_linha = df_linha.dropna(subset=["Data"])
df_time = df_linha.groupby("Data", as_index=False).agg(
    Ocupacao_Percentual=("Status", lambda s: 100 * (s == "Alugado").sum() / s.count())
)
fig_line = px.line(df_time, x="Data", y="Ocupacao_Percentual", title="Evolução da Ocupação ao Longo do Tempo", markers=True)
fig_line.update_traces(text=df_time["Ocupacao_Percentual"].round(2).astype(str) + "%", textposition="top center", mode="lines+markers+text")
st.plotly_chart(fig_line, use_container_width=True)

# --- Gráfico de Barras: Ocupação por Grupo ---
st.subheader("Taxa de Ocupação por Grupo de Carro")
df_grupo = aplicar_filtro_unidade(df_base, unit_filter)
df_grupo = df_grupo[df_grupo["Status"].isin(["Alugado", "Disponível"])]
df_group = df_grupo.groupby("Grupo", as_index=False).agg(
    Ocupacao_Percentual=("Status", lambda s: 100 * (s == "Alugado").sum() / s.count())
)
fig_bar = px.bar(df_group, x="Grupo", y="Ocupacao_Percentual", title="Taxa de Ocupação por Grupo de Carro",
                 labels={"Grupo": "Grupo", "Ocupacao_Percentual": "Ocupação (%)"},
                 text="Ocupacao_Percentual", color_discrete_sequence=px.colors.qualitative.Set2)
fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
st.plotly_chart(fig_bar, use_container_width=False)

# --- Gráficos Comparativos Básico e Especial ---
status_validos = ["Disponível", "Alugado"]
grupos_basico = ['A', 'B', 'BT', 'B+', 'C+', 'CT', 'D', 'D+']
grupos_especial = ['E+', 'F+', 'G+', 'H', 'H+', 'J+', 'O+', 'P', 'P+', 'N+', 'HD']

# Básico
st.subheader("Taxa de Ocupação dos Grupos Básicos - Comparativo")
df_basico_rec = df_base[(df_base["Unidade"] == "Rac Rec") & (df_base["Grupo"].isin(grupos_basico)) & (df_base["Status"].isin(status_validos))]
df_basico_for = df_base[(df_base["Unidade"] == "Rac For") & (df_base["Grupo"].isin(grupos_basico)) & (df_base["Status"].isin(status_validos))]
perc_basico_rec = (100 * df_basico_rec[df_basico_rec["Status"] == "Alugado"].shape[0] / df_basico_rec.shape[0]) if df_basico_rec.shape[0] > 0 else 0
perc_basico_for = (100 * df_basico_for[df_basico_for["Status"] == "Alugado"].shape[0] / df_basico_for.shape[0]) if df_basico_for.shape[0] > 0 else 0
df_ocupacao_basico = pd.DataFrame({"Unidade": ["Rac Rec", "Rac For"], "Ocupação (%)": [perc_basico_rec, perc_basico_for]})
fig_comparativo = px.bar(df_ocupacao_basico, x="Unidade", y="Ocupação (%)", title="Comparativo dos Grupos Básicos: Rac Rec vs Rac For",
                         text="Ocupação (%)", color="Unidade", color_discrete_sequence=px.colors.qualitative.Pastel1)
fig_comparativo.update_traces(texttemplate="%{text:.2f}%", textposition="inside")
st.plotly_chart(fig_comparativo, use_container_width=True)

# Especial
st.subheader("Taxa de Ocupação dos Grupos Especiais - Comparativo")
df_especial_rec = df_base[(df_base["Unidade"] == "Rac Rec") & (df_base["Grupo"].isin(grupos_especial)) & (df_base["Status"].isin(status_validos))]
df_especial_for = df_base[(df_base["Unidade"] == "Rac For") & (df_base["Grupo"].isin(grupos_especial)) & (df_base["Status"].isin(status_validos))]
perc_especial_rec = (100 * df_especial_rec[df_especial_rec["Status"] == "Alugado"].shape[0] / df_especial_rec.shape[0]) if df_especial_rec.shape[0] > 0 else 0
perc_especial_for = (100 * df_especial_for[df_especial_for["Status"] == "Alugado"].shape[0] / df_especial_for.shape[0]) if df_especial_for.shape[0] > 0 else 0
df_ocupacao_especial = pd.DataFrame({"Unidade": ["Rac Rec", "Rac For"], "Ocupação (%)": [perc_especial_rec, perc_especial_for]})
fig_comparativo_especial = px.bar(df_ocupacao_especial, x="Unidade", y="Ocupação (%)", title="Comparativo dos Grupos Especiais: Rac Rec vs Rac For",
                                  text="Ocupação (%)", color="Unidade", color_discrete_sequence=px.colors.qualitative.Pastel2)
fig_comparativo_especial.update_traces(texttemplate="%{text:.2f}%", textposition="inside")
st.plotly_chart(fig_comparativo_especial, use_container_width=True)

# Gráfico de pizza com status geral
status_counts = df_base["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Quantidade"]
fig_pie = px.pie(status_counts, names="Status", values="Quantidade", title="Distribuição de Status", hole=0.4)
st.plotly_chart(fig_pie, use_container_width=True)
