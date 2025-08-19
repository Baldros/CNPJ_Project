# Apresentação:
"""
Código de construção do app para busca de CNPJs por bairro.
"""

# Dependências:
import streamlit as st
import pandas as pd
from support_functions import search_engine_pandas, list_files

# ---------- Estado ----------
st.session_state.setdefault("result_df", None)
st.session_state.setdefault("cnpj_options", ["-- Selecione um CNPJ --"])
st.session_state.setdefault("selected_cnpj", "-- Selecione um CNPJ --")

st.set_page_config("Buscador de CNPJ por Endereço", layout="wide")
st.title("🔎 Buscador de CNPJ por Endereço")

# ---------- Aquisitando dados ----------
with st.spinner("Carregando dados..."):
    try:
        files = list_files("Dataframes", ".csv")
        df = pd.DataFrame()
        
        for file in files:
            df_temp = pd.read_csv(file, sep=";", low_memory=False)
            df = pd.concat([df, df_temp], ignore_index=True)

        if df is not None:
            bairros = df["BAIRRO"].unique()
        else:
            st.error("Não foi possível carregar os dados do arquivo.")
    except Exception as e:
        st.error(f"Erro ao processar os dados: {e}")
        df = None

# ---------- Campo de texto e botão ----------
if df is not None:
    query = st.text_input("Digite o termo para buscar:")
else:
    st.warning("Os dados ainda não foram carregados ou ocorreu um erro.")


if st.button("Buscar"):
    if not query.strip():
        st.warning("Digite algo para buscar 📌")
    elif query.upper() not in bairros:
        st.warning("Bairro não consta no conjunto de dados 📌")
    else:
        # Usar um spinner para indicar o processamento
        with st.spinner("Buscando coworkers (Isso pode demorar uns minutos)..."):
            filtros, cnpjs = search_engine_pandas(df, query.upper())
            result_por_logradouro = {}

            # Processar os filtros e segmentar por logradouro
            for filtro in filtros.values():
                if isinstance(filtro, pd.DataFrame):
                    # Agrupar por logradouro
                    for logradouro, group in filtro.groupby("LOGRADOURO"):
                        if logradouro not in result_por_logradouro:
                            result_por_logradouro[logradouro] = group
                        else:
                            result_por_logradouro[logradouro] = pd.concat(
                                [result_por_logradouro[logradouro], group],
                                axis=0,
                                ignore_index=True,
                            )
                else:
                    st.warning(f"Filtro inválido encontrado: {type(filtro)}")
                    continue

            # Finalizar o spinner automaticamente ao sair do bloco
            st.success("Busca concluída!")

            # Armazenar o resultado no estado da sessão
            st.session_state["result_df"] = result_por_logradouro
# ---------- Exibir resultados por logradouro ----------
if st.session_state["result_df"] is not None:
    st.subheader("Resultados da Busca por Logradouro")
    for logradouro, df_logradouro in st.session_state["result_df"].items():
        # Criar a coluna CNPJ combinando as partes
        df_logradouro["CNPJ"] = (
            df_logradouro["CNPJ BÁSICO"].astype(str).str.zfill(8) +  # Preencher com zeros à esquerda
            df_logradouro["CNPJ ORDEM"].astype(str).str.zfill(4) +        # Preencher com zeros à esquerda
            df_logradouro["CNPJ DV"].astype(str).str.zfill(2)            # Preencher com zeros à esquerda
        )
        df_logradouro = df_logradouro.drop_duplicates(subset=["CNPJ"]) # Remover duplicatas baseadas no CNPJ
        df_logradouro = df_logradouro.sort_values(by=["NÚMERO"]) # Ordenando valores por número
        df_logradouro = df_logradouro.fillna("Não informado")  # Preencher NaN com string vazia
        
        # Selecionar as colunas para exibição
        with st.expander(f"Logradouro: {logradouro}"):
            st.dataframe(df_logradouro[[
                "CNPJ", "CORREIO ELETRÔNICO","TIPO DE LOGRADOURO", "LOGRADOURO", "BAIRRO", "NÚMERO", "COMPLEMENTO",
            ]].astype(str))
