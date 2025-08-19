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
    return [str(p.resolve()) for p in base.rglob(pattern) if p.is_file()]
 
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
    for complemento in complementos:
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
