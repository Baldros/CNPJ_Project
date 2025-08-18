import polars as pl
from tqdm import tqdm
from pathlib import Path
from typing import List, Optional
import re

def list_files(dir_path: str, extension: Optional[str] = None, recursive: bool = True) -> List[str]:
    """
    Lista todos os arquivos no diretório `dir_path`.
    Se `extension` for fornecida (ex: 'csv' ou '.csv'),
    filtra apenas arquivos com essa extensão.
    Por padrão, pesquisa recursivamente (subpastas).
    """
    base = Path(dir_path)
    if extension:
        ext = extension if extension.startswith('.') else f".{extension}"
        pattern = f"**/*{ext}" if recursive else f"*{ext}"
    else:
        pattern = "**/*" if recursive else "*"
    return [str(p.resolve()) for p in tqdm(base.rglob(pattern), desc="Lendo arquivos...") if p.is_file()]
 

def search_engine_polars(query: str, files: list, column: str = "BAIRRO", exact_match: bool = True):
    """
    Busca por 'query' na coluna especificada em todos os arquivos listados.
    Pode fazer busca exata ou por substring (case-insensitive).
    """
    q_lower = query.lower()
    dfs = []

    for arquivo in tqdm(files, desc="Buscando"):
        df = pl.read_csv(
            arquivo,
            separator=";",
            encoding="utf8-lossy",
            infer_schema=False,
        )
        
        df = df.with_columns(pl.col(column).cast(pl.Utf8))

        # Se busca exata
        if exact_match:
            df_match = df.filter(pl.col(column).str.to_lowercase() == q_lower)
            
        # Se busca por substring
        else:
            df_match = df.filter(pl.col(column).str.to_lowercase().str.contains(q_lower))

        if df_match.height > 0:
            df_match = df_match.with_columns(pl.lit(arquivo.split("\\")[-1]).alias("_arquivo"))
            dfs.append(df_match)
    
    return pl.concat(dfs, how="vertical") if dfs else pl.DataFrame({}, schema=[column])

def cleaner(valor: str, tamanho: int) -> str:
    """Remove tudo que não for número e aplica zfill."""
    return re.sub(r"\D", "", str(valor)).zfill(tamanho)

def search_engine_pandas(dataframe, bairro):
    """
    Mecanismo de busca de Coworkers por bairro.
    """
    
    dfRegional = dataframe[dataframe["BAIRRO"] == bairro]
    complementos = set(dfRegional["COMPLEMENTO"].unique())
    filtros = {}
    cnpjs = []
    for complemento in tqdm(complementos):
        # Usar regex=False para evitar problemas com caracteres especiais
        filtro_n1 = dfRegional[dfRegional["COMPLEMENTO"].str.contains(complemento, case=False, na=False, regex=False)]
        logradouros = filtro_n1["LOGRADOURO"].unique()
        for logradouro in logradouros:
            filtro_n2 = filtro_n1[filtro_n1["LOGRADOURO"] == logradouro]
            numeros = filtro_n2["NÚMERO"].unique()
            for numero in numeros:
                filtro_n3 = filtro_n2[filtro_n2["NÚMERO"] == numero]
                if len(filtro_n3) > 1:
                    filtros[complemento] = filtro_n3
                    for row in filtro_n3.itertuples():
                         cnpjs.append(
                                    f"{cleaner(row._1, 8)}{cleaner(row._2, 4)}{cleaner(row._3, 2)}"
                                )
    return filtros, cnpjs