import pandas as pd
import os
from glob import glob
import re

# Caminho da pasta onde estão os arquivos CSV
pasta_dados = r"C:\Users\Alane Souza\Bases Ocupação Semanal"

# Lista todos os arquivos CSV na pasta
arquivos_csv = sorted(glob(os.path.join(pasta_dados, "*.csv")))

# Lista para armazenar os DataFrames
dataframes = []

for arquivo in arquivos_csv:
    df = pd.read_csv(arquivo)

    # Filtrar apenas "Rac For" e "Rac Rec"
    df = df[df['Unidade'].isin(['Rac For', 'Rac Rec'])]

    # Remover "Observacoes" se existir
    if 'Observacoes' in df.columns:
        df = df.drop(columns=['Observacoes'])

    # Extrair a data do nome do arquivo (formato dd-mm-yyyy) 
    match = re.search(r"(\d{2})-(\d{2})-(\d{4})", os.path.basename(arquivo))
    if match:
        data_arquivo = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
    else:
        data_arquivo = ""

    # Criar a coluna "Nome Da Origem"
    df["Nome Da Origem"] = data_arquivo

    dataframes.append(df)

# Junta tudo
df_final = pd.concat(dataframes, ignore_index=True)

# Normaliza espaços e texto
df_final['Grupo'] = df_final['Grupo'].astype(str).str.strip()
df_final['Status'] = df_final['Status'].astype(str).str.strip()

# Remove duplicatas mantendo Alugado como prioridade
df_final['status_prioridade'] = df_final['Status'].apply(lambda x: 0 if x == 'Alugado' else 1)
df_final = df_final.sort_values(by=['Nome Da Origem', 'Placa', 'status_prioridade'])
df_final = df_final.drop_duplicates(subset=['Nome Da Origem', 'Placa'], keep='first')
df_final = df_final.drop(columns=['status_prioridade'])

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

# Função para cálculo geral por unidade
def calcular_ocupacao_geral(df, unidade=None):
    df_filtrado = df[df['Status'].isin(status_validos)]
    if unidade:
        df_filtrado = df_filtrado[df_filtrado['Unidade'] == unidade]
    alugado = df_filtrado[df_filtrado['Status'] == 'Alugado'].shape[0]
    total = df_filtrado.shape[0]
    ocupacao = (alugado / total * 100) if total > 0 else 0
    return ocupacao, alugado, total

# Cálculos por grupo
rec_basico, rec_basico_alugado, rec_basico_total = calcular_ocupacao(df_final, 'Rac Rec', grupos_basico)
rec_especial, rec_especial_alugado, rec_especial_total = calcular_ocupacao(df_final, 'Rac Rec', grupos_especial)

for_basico, for_basico_alugado, for_basico_total = calcular_ocupacao(df_final, 'Rac For', grupos_basico)
for_especial, for_especial_alugado, for_especial_total = calcular_ocupacao(df_final, 'Rac For', grupos_especial)

# Impressão por grupo
print(f"Rac Rec - Básico: {rec_basico:.2f}% ({rec_basico_alugado} de {rec_basico_total})")
print(f"Rac Rec - Especial: {rec_especial:.2f}% ({rec_especial_alugado} de {rec_especial_total})")
print(f"Rac For - Básico: {for_basico:.2f}% ({for_basico_alugado} de {for_basico_total})")
print(f"Rac For - Especial: {for_especial:.2f}% ({for_especial_alugado} de {for_especial_total})")

# GERAL BÁSICO
df_basico = df_final[
    (df_final['Grupo'].isin(grupos_basico)) &
    (df_final['Status'].isin(status_validos))
]
total_basico = df_basico.shape[0]
alugado_basico = df_basico[df_basico['Status'] == 'Alugado'].shape[0]
perc_basico = (alugado_basico / total_basico * 100) if total_basico > 0 else 0

# GERAL ESPECIAL
df_especial = df_final[
    (df_final['Grupo'].isin(grupos_especial)) &
    (df_final['Status'].isin(status_validos))
]
total_especial = df_especial.shape[0]
alugado_especial = df_especial[df_especial['Status'] == 'Alugado'].shape[0]
perc_especial = (alugado_especial / total_especial * 100) if total_especial > 0 else 0

# Média simples dos percentuais de ocupação (como no Excel)
perc_basico_media_simples = (rec_basico + for_basico) / 2
perc_especial_media_simples = (rec_especial + for_especial) / 2


# Impressão
print(f"TOTAL GERAL - Básico: {perc_basico:.2f}% ({alugado_basico} de {total_basico})")
print(f"TOTAL GERAL - Especial: {perc_especial:.2f}% ({alugado_especial} de {total_especial})")
print(f"TOTAL GERAL - Básico (média simples REC/FOR): {perc_basico_media_simples:.2f}%")
print(f"TOTAL GERAL - Especial (média simples REC/FOR): {perc_especial_media_simples:.2f}%")

# Exporta resultado final
df_final.to_excel(os.path.join("Base", "base_tratada.xlsx"), index=False)
print(f"Processamento finalizado! Total de linhas: {df_final.shape[0]}")
