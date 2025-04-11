import pandas as pd
import os

# Caminho do arquivo tratado
caminho_base = os.path.join("Base", "base_tratada.xlsx")

# Verifica se o arquivo existe
if not os.path.exists(caminho_base):
    raise FileNotFoundError(f"O arquivo {caminho_base} não foi encontrado. Execute o tratar_base.py primeiro.")

# Lê a base tratada
df_final = pd.read_excel(caminho_base)

# Grupos definidos
grupos_basico = ['A', 'B', 'BT', 'B+', 'C+', 'CT', 'D', 'D+']
grupos_especial = ['E+', 'F+', 'G+', 'H', 'H+', 'J+', 'O+', 'P', 'P+', 'N+', 'HD']
status_validos = ['Disponível', 'Alugado']

# Função para cálculo por grupo e unidade
def calcular_ocupacao(df, unidade, grupos_alvo):
    df_filtrado = df[
        (df['Unidade'] == unidade) &
        (df['Grupo'].notna()) &
        (df['Grupo'].isin(grupos_alvo)) &
        (df['Status'].isin(status_validos))
    ]
    alugado = df_filtrado[df_filtrado['Status'] == 'Alugado'].shape[0]
    total = df_filtrado.shape[0]
    ocupacao = (alugado / total * 100) if total > 0 else 0
    return ocupacao, alugado, total

# Cálculos
rec_basico, rec_basico_alugado, rec_basico_total = calcular_ocupacao(df_final, 'Rac Rec', grupos_basico)
rec_especial, rec_especial_alugado, rec_especial_total = calcular_ocupacao(df_final, 'Rac Rec', grupos_especial)

for_basico, for_basico_alugado, for_basico_total = calcular_ocupacao(df_final, 'Rac For', grupos_basico)
for_especial, for_especial_alugado, for_especial_total = calcular_ocupacao(df_final, 'Rac For', grupos_especial)

# Cálculo TOTAL GERAL
geral_basico = rec_basico_alugado + for_basico_alugado
geral_basico_total = rec_basico_total + for_basico_total
geral_basico_perc = (geral_basico / geral_basico_total * 100) if geral_basico_total > 0 else 0

geral_especial = rec_especial_alugado + for_especial_alugado
geral_especial_total = rec_especial_total + for_especial_total
geral_especial_perc = (geral_especial / geral_especial_total * 100) if geral_especial_total > 0 else 0

# Criação da tabela de resumo
resumo_ocupacao = pd.DataFrame([
    {"Unidade": "Rac Rec", "Grupo": "Básico", "Ocupação (%)": round(rec_basico, 2), "Alugados": rec_basico_alugado, "Qtd. Total": rec_basico_total},
    {"Unidade": "Rac Rec", "Grupo": "Especial", "Ocupação (%)": round(rec_especial, 2), "Alugados": rec_especial_alugado, "Qtd. Total": rec_especial_total},
    {"Unidade": "Rac For", "Grupo": "Básico", "Ocupação (%)": round(for_basico, 2), "Alugados": for_basico_alugado, "Qtd. Total": for_basico_total},
    {"Unidade": "Rac For", "Grupo": "Especial", "Ocupação (%)": round(for_especial, 2), "Alugados": for_especial_alugado, "Qtd. Total": for_especial_total},
    {"Unidade": "Total Geral", "Grupo": "Básico", "Ocupação (%)": round(geral_basico_perc, 2), "Alugados": geral_basico, "Qtd. Total": geral_basico_total},
    {"Unidade": "Total Geral", "Grupo": "Especial", "Ocupação (%)": round(geral_especial_perc, 2), "Alugados": geral_especial, "Qtd. Total": geral_especial_total},
])

# Exporta para a pasta Base
resumo_path = os.path.join("Base", "resumo_ocupacao.xlsx")
resumo_ocupacao.to_excel(resumo_path, index=False)

# Exibe no console
print("\nResumo de Ocupação por Unidade e Grupo:")
print(resumo_ocupacao)
print(f"\nResumo salvo em: {resumo_path}")
