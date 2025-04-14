import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Função para carregamento dos dados
@st.cache_data
def load_data():
    # Os arquivos devem estar na mesma pasta do dashboard.py
    base_path = "base_tratada.xlsx"
    resumo_path = "resumo_ocupacao.xlsx"
    
    df_base = pd.read_excel(base_path)
    resumo = pd.read_excel(resumo_path)
    
    return df_base, resumo

# Carrega os dados originais
df_base, resumo = load_data()

# --- Filtro na Sidebar (apenas afeta os gráficos) ---
st.sidebar.header("Filtro por Unidade")
unit_options = ["Todos", "Rac Rec", "Rac For"]
unit_filter = st.sidebar.selectbox("Selecione a Unidade", unit_options)

if unit_filter != "Todos":
    df_filtered = df_base[df_base["Unidade"] == unit_filter].copy()
else:
    df_filtered = df_base.copy()

st.markdown(
    """
    <style>
    h1 {
        font-size: 33px !important;
    }
    </style>
    """, unsafe_allow_html=True
)
# Título do Dashboard
st.title("Dashboard Resumo de Ocupação")


st.markdown(
    """
    <style>
    h3 {
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True
)
# --- KPIs (dados completos, não filtrados) ---
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

# --- KPIs Totais Gerais (dados completos, não filtrados) ---
#st.subheader("KPIs Totais Gerais")
# Definindo os grupos para o cálculo
grupos_basico = ['A', 'B', 'BT', 'B+', 'C+', 'CT', 'D', 'D+']
grupos_especial = ['E+', 'F+', 'G+', 'H', 'H+', 'J+', 'O+', 'P', 'P+', 'N+', 'HD']
status_validos = ['Disponível', 'Alugado']

# Cálculo para grupo Básico
df_basico_calc = df_base[(df_base["Grupo"].isin(grupos_basico)) & (df_base["Status"].isin(status_validos))]
total_basico = df_basico_calc.shape[0]
alugado_basico = df_basico_calc[df_basico_calc["Status"] == "Alugado"].shape[0]
perc_basico = (alugado_basico / total_basico * 100) if total_basico > 0 else 0

# Cálculo para grupo Especial
df_especial_calc = df_base[(df_base["Grupo"].isin(grupos_especial)) & (df_base["Status"].isin(status_validos))]
total_especial = df_especial_calc.shape[0]
alugado_especial = df_especial_calc[df_especial_calc["Status"] == "Alugado"].shape[0]
perc_especial = (alugado_especial / total_especial * 100) if total_especial > 0 else 0

# col_tot1, col_tot2 = st.columns(2)
# with col_tot1:
#     st.metric("Total Geral - Básico", f"{perc_basico:.2f}%")
# with col_tot2:
#     st.metric("Total Geral - Especial", f"{perc_especial:.2f}%")

# Logo após os KPIs Totais Gerais

st.subheader("Tabela de Resumo de Ocupação")

# Aqui selecionamos as colunas que você deseja exibir.
# Caso os nomes sejam diferentes, ajuste conforme o DataFrame `resumo`.
# Se você quiser exibir exatamente as colunas: Unidade, Grupo, Ocupação (%), Alugados, Qtd. Total,
# certifique-se de que elas existam no DataFrame "resumo".

colunas_desejadas = ["Unidade", "Grupo", "Ocupação (%)", "Alugados", "Qtd. Total"]

# Crie uma cópia contendo apenas as colunas desejadas (se elas existirem no arquivo)
df_tabela = resumo[colunas_desejadas].copy()

# Caso queira formatar o valor de "Ocupação (%)" com 2 casas decimais:
df_tabela["Ocupação (%)"] = df_tabela["Ocupação (%)"].map(lambda x: f"{x:.2f}")

# Exiba a tabela
st.dataframe(df_tabela)

    

# --- Gráfico de Linhas para Evolução da Ocupação ---
st.subheader("Evolução da Ocupação")
# Converte a coluna "Nome Da Origem" para data com os dados filtrados
df_filtered["Data"] = pd.to_datetime(df_filtered["Nome Da Origem"], format='%d/%m/%Y', errors='coerce')
df_time = df_filtered.dropna(subset=["Data"])

# Usando groupby.agg para calcular a taxa de ocupação por data:
df_time = df_time.groupby("Data", as_index=False).agg(
    Ocupacao_Percentual=("Status", lambda s: 100 * (s == "Alugado").sum() / s.count())
)
df_time = df_time.sort_values("Data")

fig_line = px.line(
    df_time,
    x="Data",
    y="Ocupacao_Percentual",
    title="Evolução da Ocupação ao Longo do Tempo",
    markers=True,
    labels={"Ocupacao_Percentual": "Ocupação (%)", "Data": "Data"}
)
fig_line.update_traces(
    text=df_time["Ocupacao_Percentual"].round(2).astype(str) + "%",
    textposition="top center",
    mode='lines+markers+text'
)
st.plotly_chart(fig_line, use_container_width=True)

# --- Gráfico de Barras: Taxa de Ocupação por Grupo de Carro ---
st.subheader("Taxa de Ocupação por Grupo de Carro")
# Usando groupby.agg para calcular a taxa de ocupação por Grupo:
df_group = df_filtered.groupby("Grupo", as_index=False).agg(
    Ocupacao_Percentual=("Status", lambda s: 100 * (s == "Alugado").sum() / s.count())
)

fig_bar = px.bar(
    df_group,
    x="Grupo",
    y="Ocupacao_Percentual",
    title="Taxa de Ocupação por Grupo de Carro",
    labels={"Grupo": "Grupo", "Ocupacao_Percentual": "Ocupação (%)"},
    text="Ocupacao_Percentual",
    color_discrete_sequence=px.colors.qualitative.Set2,
    width=1200,
    height=400,
)
fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
st.plotly_chart(fig_bar, use_container_width=False)


# --- Novo Gráfico: Comparativo Ocupação dos Grupos Básicos ---
st.subheader("Taxa de Ocupação dos Grupos Básicos - Comparativo")
# Para os grupos básicos, usamos os dados do df_base (total) com status válidos.
df_basico_rec = df_base[(df_base["Unidade"] == "Rac Rec") & 
                        (df_base["Grupo"].isin(grupos_basico)) & 
                        (df_base["Status"].isin(status_validos))]
perc_basico_rec = (100 * df_basico_rec[df_basico_rec["Status"] == "Alugado"].shape[0] / df_basico_rec.shape[0]) if df_basico_rec.shape[0] > 0 else 0

df_basico_for = df_base[(df_base["Unidade"] == "Rac For") & 
                        (df_base["Grupo"].isin(grupos_basico)) & 
                        (df_base["Status"].isin(status_validos))]
perc_basico_for = (100 * df_basico_for[df_basico_for["Status"] == "Alugado"].shape[0] / df_basico_for.shape[0]) if df_basico_for.shape[0] > 0 else 0

df_ocupacao_basico = pd.DataFrame({
    "Unidade": ["Rac Rec", "Rac For"],
    "Ocupação (%)": [perc_basico_rec, perc_basico_for]
})

fig_comparativo = px.bar(
    df_ocupacao_basico,
    x="Unidade",
    y="Ocupação (%)",
    title="Comparativo dos Grupos Básicos: Rac Rec vs Rac For",
    text="Ocupação (%)",
    color="Unidade",
    color_discrete_sequence=px.colors.qualitative.Pastel1,
    width=500,
    height=350
)
fig_comparativo.update_traces(texttemplate="%{text:.2f}%", textposition="inside")
st.plotly_chart(fig_comparativo, use_container_width=True)

# --- Novo Gráfico: Comparativo Ocupação dos Grupos Especiais ---
st.subheader("Taxa de Ocupação dos Grupos Especiais - Comparativo")
# Para os grupos especiais
df_especial_rec = df_base[(df_base["Unidade"] == "Rac Rec") & 
                          (df_base["Grupo"].isin(grupos_especial)) & 
                          (df_base["Status"].isin(status_validos))]
perc_especial_rec = (100 * df_especial_rec[df_especial_rec["Status"] == "Alugado"].shape[0] / df_especial_rec.shape[0]) if df_especial_rec.shape[0] > 0 else 0

df_especial_for = df_base[(df_base["Unidade"] == "Rac For") & 
                          (df_base["Grupo"].isin(grupos_especial)) & 
                          (df_base["Status"].isin(status_validos))]
perc_especial_for = (100 * df_especial_for[df_especial_for["Status"] == "Alugado"].shape[0] / df_especial_for.shape[0]) if df_especial_for.shape[0] > 0 else 0

df_ocupacao_especial = pd.DataFrame({
    "Unidade": ["Rac Rec", "Rac For"],
    "Ocupação (%)": [perc_especial_rec, perc_especial_for]
})

fig_comparativo_especial = px.bar(
    df_ocupacao_especial,
    x="Unidade",
    y="Ocupação (%)",
    title="Comparativo dos Grupos Especiais: Rac Rec vs Rac For",
    text="Ocupação (%)",
    color="Unidade",
    color_discrete_sequence=px.colors.qualitative.Pastel2,
    width=500,
    height=350
)
fig_comparativo_especial.update_traces(texttemplate="%{text:.2f}%", textposition="inside")
st.plotly_chart(fig_comparativo_especial, use_container_width=True)

status_counts = df_base["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Quantidade"]

fig_pie = px.pie(status_counts, names="Status", values="Quantidade",
                 title="Distribuição de Status",
                 hole=0.4)  # formato donut
st.plotly_chart(fig_pie, use_container_width=True)


