"""
Serviço de IA para padronização de dados
"""
import re
import logging
from typing import Any, List, Dict, Optional, Tuple, Union
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_similarity(str1: str, str2: str) -> float:
    """Calcula similaridade entre duas strings (0-1)"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def detect_and_convert_date(value: Any) -> Optional[str]:
    """
    Detecta e converte data para formato ISO (YYYY-MM-DD)
    Suporta: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD/MM/YY, datas em texto
    """
    if pd.isna(value) or value is None:
        return None
    
    # Se já for datetime, converter direto
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    
    # Converter para string e limpar
    date_str = str(value).strip()
    
    # Padrões de data
    patterns = [
        # DD/MM/YYYY ou DD-MM-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
        # YYYY-MM-DD ou YYYY/MM/DD
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),
        # DD/MM/YY ou DD-MM-YY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})', 'dmy_short'),
    ]
    
    for pattern, fmt in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                if fmt == 'dmy':
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return f"{year:04d}-{month:02d}-{day:02d}"
                elif fmt == 'ymd':
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return f"{year:04d}-{month:02d}-{day:02d}"
                elif fmt == 'dmy_short':
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    year += 2000 if year < 50 else 1900
                    return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                continue
    
    # Tentar datas em texto (ex: "15 de março de 2024")
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    texto_pattern = r'(\d{1,2})\s*de\s*([a-zA-Zç]+)\s*de\s*(\d{4})'
    match = re.match(texto_pattern, date_str.lower())
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        month = meses.get(month_name)
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"
    
    return None


def detect_and_convert_currency(value: Any) -> Optional[float]:
    """
    Detecta e converte valor monetário para float de forma robusta.
    Suporta formatos brasileiros e americanos, e valores puros de Excel.
    """
    if pd.isna(value) or value is None:
        return None
    
    # Se for número (float/int), retornar direto
    if isinstance(value, (int, float)):
        return float(value)
    
    # Converter para string e limpar símbolos
    val_s = str(value).strip().replace('R$', '').replace('$', '').strip()
    if not val_s:
        return None
        
    # Lógica de decisão de separador decimal
    # Se tiver vírgula e ponto, o último é o decimal
    if ',' in val_s and '.' in val_s:
        if val_s.rfind(',') > val_s.rfind('.'):
            # BR: 1.234,56
            val_s = val_s.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56
            val_s = val_s.replace(',', '')
    elif ',' in val_s:
        # Só vírgula: se tem 1 ou 2 casas, é decimal. Se tem 3 e não é final, é milhar.
        parts = val_s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            val_s = val_s.replace(',', '.')
        else:
            val_s = val_s.replace(',', '')
    elif '.' in val_s:
        # Só ponto: se tem 1 ou 2 casas, é decimal. Se tem mais de 2, pode ser milhar sem decimal.
        parts = val_s.split('.')
        if len(parts) == 2 and len(parts[1]) > 2:
            val_s = val_s.replace('.', '')
            
    try:
        return float(val_s)
    except ValueError:
        return None


def validate_cnpj(cnpj: str) -> bool:
    """Valida dígitos verificadores do CNPJ"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # Verificar sequências repetidas
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcular primeiro dígito
    multiplicadores = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Calcular segundo dígito
    multiplicadores = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cnpj[13]) == digito2


def detect_and_convert_cnpj(value: Any) -> Optional[str]:
    """
    Padroniza CNPJ para formato: 00.000.000/0000-00
    """
    if pd.isna(value) or value is None:
        return None
    
    # Remover tudo que não é dígito
    cnpj = re.sub(r'[^0-9]', '', str(value))
    
    if len(cnpj) != 14:
        return None
    
    # Validar dígitos verificadores
    if not validate_cnpj(cnpj):
        return None
    
    # Formatar
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def validate_cpf(cpf: str) -> bool:
    """Valida dígitos verificadores do CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    # Verificar sequências repetidas
    if cpf == cpf[0] * 11:
        return False
    
    # Calcular primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Calcular segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2


def detect_and_convert_cpf(value: Any) -> Optional[str]:
    """
    Padroniza CPF para formato: 000.000.000-00
    """
    if pd.isna(value) or value is None:
        return None
    
    # Remover tudo que não é dígito
    cpf = re.sub(r'[^0-9]', '', str(value))
    
    if len(cpf) != 11:
        return None
    
    # Validar dígitos verificadores
    if not validate_cpf(cpf):
        return None
    
    # Formatar
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def suggest_category(description: str, categories: List[str]) -> Dict[str, Any]:
    """
    Sugere categoria baseada na descrição usando similaridade de texto
    """
    if not description or not categories:
        return {"category": None, "confidence": 0.0}
    
    best_match = None
    best_score = 0.0
    
    for category in categories:
        score = calculate_similarity(description, category)
        if score > best_score:
            best_score = score
            best_match = category
    
    # Calcular nível de confiança
    if best_score >= 0.7:
        confidence_level = "high"
    elif best_score >= 0.4:
        confidence_level = "medium"
    else:
        confidence_level = "low"
    
    return {
        "category": best_match,
        "similarity": best_score,
        "confidence": confidence_level,
        "alternatives": [
            {"category": cat, "score": calculate_similarity(description, cat)}
            for cat in categories
            if cat != best_match
        ][:3]  # Top 3 alternativas
    }


def detect_data_type(column_values: pd.Series) -> Dict[str, Any]:
    """
    Analisa uma coluna e detecta o tipo de dado
    Retorna: {"type": "date|currency|cnpj|cpf|number|text|boolean", "confidence": 0.0-1.0}
    """
    # Remover valores nulos
    values = column_values.dropna()
    if len(values) == 0:
        return {"type": "text", "confidence": 0.0}
    
    # Amostra para análise (máximo 100 valores)
    sample = values.head(100)
    total = len(sample)
    
    # Contadores para cada tipo
    counts = {
        "date": 0,
        "currency": 0,
        "cnpj": 0,
        "cpf": 0,
        "number": 0,
        "boolean": 0,
        "text": 0
    }
    
    for value in sample:
        value_str = str(value).strip()
        
        # Verificar booleano
        if value_str.lower() in ['true', 'false', 'sim', 'não', 'nao', 'yes', 'no', '1', '0']:
            counts["boolean"] += 1
            continue
        
        # Verificar data
        if detect_and_convert_date(value) is not None:
            counts["date"] += 1
            continue
        
        # Verificar CNPJ
        if detect_and_convert_cnpj(value) is not None:
            counts["cnpj"] += 1
            continue
        
        # Verificar CPF
        if detect_and_convert_cpf(value) is not None:
            counts["cpf"] += 1
            continue
        
        # Verificar moeda
        if detect_and_convert_currency(value) is not None:
            counts["currency"] += 1
            continue
        
        # Verificar número
        try:
            float(value_str.replace(',', '.'))
            counts["number"] += 1
            continue
        except ValueError:
            pass
        
        # Se chegou aqui, é texto
        counts["text"] += 1
    
    # Encontrar tipo mais comum
    max_type = max(counts, key=counts.get)
    max_count = counts[max_type]
    confidence = max_count / total
    
    # Estatísticas adicionais
    unique_count = values.nunique()
    empty_count = column_values.isna().sum()
    
    return {
        "type": max_type,
        "confidence": confidence,
        "statistics": {
            "total_values": len(column_values),
            "non_null_values": len(values),
            "unique_values": int(unique_count),
            "empty_values": int(empty_count),
            "type_distribution": {k: v/total for k, v in counts.items()}
        }
    }


def clean_dataframe(df: pd.DataFrame, column_types: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Limpa e padroniza todo o DataFrame
    Retorna: (DataFrame limpo, relatório de limpeza)
    """
    df_clean = df.copy()
    report = {
        "columns_processed": [],
        "errors": [],
        "warnings": []
    }
    
    for column in df_clean.columns:
        # Detectar tipo se não fornecido
        if column_types and column in column_types:
            detected_type = column_types[column]
        else:
            detection = detect_data_type(df_clean[column])
            detected_type = detection["type"]
        
        column_report = {
            "column": column,
            "detected_type": detected_type,
            "converted_values": 0,
            "null_values": 0,
            "errors": []
        }
        
        # Aplicar conversão baseada no tipo
        try:
            if detected_type == "date":
                df_clean[column] = df_clean[column].apply(detect_and_convert_date)
                column_report["converted_values"] = df_clean[column].notna().sum()
            elif detected_type == "currency":
                df_clean[column] = df_clean[column].apply(detect_and_convert_currency)
                column_report["converted_values"] = df_clean[column].notna().sum()
            elif detected_type == "cnpj":
                df_clean[column] = df_clean[column].apply(detect_and_convert_cnpj)
                column_report["converted_values"] = df_clean[column].notna().sum()
            elif detected_type == "cpf":
                df_clean[column] = df_clean[column].apply(detect_and_convert_cpf)
                column_report["converted_values"] = df_clean[column].notna().sum()
            elif detected_type == "number":
                df_clean[column] = pd.to_numeric(df_clean[column].astype(str).str.replace(',', '.'), errors='coerce')
                column_report["converted_values"] = df_clean[column].notna().sum()
            elif detected_type == "boolean":
                def to_bool(x):
                    if pd.isna(x):
                        return None
                    return str(x).lower() in ['true', 'sim', 'yes', '1']
                df_clean[column] = df_clean[column].apply(to_bool)
                column_report["converted_values"] = df_clean[column].notna().sum()
            
            column_report["null_values"] = df_clean[column].isna().sum()
            
        except Exception as e:
            column_report["errors"].append(str(e))
            report["errors"].append(f"Erro ao processar coluna {column}: {str(e)}")
        
        report["columns_processed"].append(column_report)
    
    return df_clean, report


def find_similar_columns(source_columns: List[str], target_columns: List[str], threshold: float = 0.6) -> Dict[str, str]:
    """
    Encontra correspondências entre colunas baseado em similaridade de nomes
    """
    mappings = {}
    
    for source in source_columns:
        best_match = None
        best_score = 0.0
        
        for target in target_columns:
            score = calculate_similarity(source, target)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = target
        
        if best_match:
            mappings[source] = best_match
    
    return mappings


class DataCleaningService:
    """Serviço unificado de limpeza de dados"""
    
    def __init__(self):
        self.history = []
    
    def clean(self, df: pd.DataFrame, column_types: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, Dict]:
        """Limpa DataFrame e registra no histórico"""
        df_clean, report = clean_dataframe(df, column_types)
        self.history.append({
            "operation": "clean",
            "input_shape": df.shape,
            "output_shape": df_clean.shape,
            "report": report
        })
        return df_clean, report
    
    def detect_types(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Detecta tipos de todas as colunas"""
        result = {}
        for column in df.columns:
            result[column] = detect_data_type(df[column])
        return result
    
    def suggest_mappings(self, source_cols: List[str], target_cols: List[str]) -> Dict[str, str]:
        """Sugere mapeamentos de colunas"""
        return find_similar_columns(source_cols, target_cols)
    
    def categorize(self, descriptions: List[str], categories: List[str]) -> List[Dict]:
        """Categoriza múltiplas descrições"""
        return [suggest_category(desc, categories) for desc in descriptions]
    
    def get_history(self) -> List[Dict]:
        """Retorna histórico de operações"""
        return self.history


# ============================================================================
# FUNÇÕES ESPECÍFICAS PARA CLIENTES, ORÇAMENTOS E CONTRATOS
# ============================================================================

def extract_cliente_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de clientes de planilhas com estrutura específica
    como a do arquivo ClientesTodos.xlsx
    """
    clientes = []
    cliente_atual = {}
    
    for idx, row in df.iterrows():
        # Verificar se é linha de nome (primeira coluna vazia, segunda com nome)
        if pd.notna(row.iloc[1]) and (pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == ''):
            nome = str(row.iloc[1]).strip()
            if nome and not nome.startswith('RG/') and not nome.startswith('Endereço:') and not nome.startswith('Sem contato'):
                # Salvar cliente anterior se existir
                if cliente_atual and 'nome' in cliente_atual:
                    clientes.append(cliente_atual.copy())
                
                # Iniciar novo cliente
                cliente_atual = {'nome': nome}
        
        # Extrair CPF/CNPJ
        if 'CPF/CNPJ:' in str(row.values):
            for val in row.values:
                if pd.notna(val) and 'CPF/CNPJ:' in str(val):
                    cpf_cnpj = str(val).split('CPF/CNPJ:')[1].strip()
                    cliente_atual['cpf_cnpj'] = cpf_cnpj
        
        # Extrair RG/IE
        if 'RG/Inscrição Estadual:' in str(row.values):
            for val in row.values:
                if pd.notna(val) and 'RG/Inscrição Estadual:' in str(val):
                    rg_ie = str(val).split('RG/Inscrição Estadual:')[1].strip()
                    cliente_atual['rg_ie'] = rg_ie
        
        # Extrair Telefone
        if 'Telefone:' in str(row.values):
            for val in row.values:
                if pd.notna(val) and 'Telefone:' in str(val):
                    telefone = str(val).split('Telefone:')[1].strip()
                    cliente_atual['telefone'] = telefone
        
        # Extrair Endereço
        if 'Endereço:' in str(row.values):
            for val in row.values:
                if pd.notna(val) and 'Endereço:' in str(val):
                    endereco = str(val).split('Endereço:')[1].strip()
                    cliente_atual['endereco'] = endereco
        
        # Extrair Status (ATIVO/INATIVO)
        if len(row) > 8 and pd.notna(row.iloc[8]) and str(row.iloc[8]).strip() in ['ATIVO', 'INATIVO']:
            cliente_atual['status'] = str(row.iloc[8]).strip()
        
        # Extrair contatos
        if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip() == 'Contato':
            # Próxima linha tem os dados do contato
            if idx + 1 < len(df):
                next_row = df.iloc[idx + 1]
                if pd.notna(next_row.iloc[1]):
                    cliente_atual['contato_nome'] = str(next_row.iloc[1]).strip()
                if pd.notna(next_row.iloc[2]):
                    cliente_atual['contato_telefone'] = str(next_row.iloc[2]).strip()
                if len(next_row) > 4 and pd.notna(next_row.iloc[4]):
                    cliente_atual['contato_email'] = str(next_row.iloc[4]).strip()
                if len(next_row) > 7 and pd.notna(next_row.iloc[7]):
                    cliente_atual['contato_tipo'] = str(next_row.iloc[7]).strip()
    
    # Adicionar último cliente
    if cliente_atual and 'nome' in cliente_atual:
        clientes.append(cliente_atual)
    
    # Criar DataFrame
    if not clientes:
        return pd.DataFrame()
        
    df_clientes = pd.DataFrame(clientes)
    
    # Limpar CPF/CNPJ
    if 'cpf_cnpj' in df_clientes.columns:
        df_clientes['cpf_cnpj'] = df_clientes['cpf_cnpj'].apply(
            lambda x: detect_and_convert_cnpj(x) if pd.notna(x) and len(str(x).replace('.', '').replace('-', '').replace('/', '')) == 14 
            else detect_and_convert_cpf(x) if pd.notna(x) and len(str(x).replace('.', '').replace('-', '').replace('/', '')) == 11
            else x
        )
    
    return df_clientes


def _find_value_below(df: pd.DataFrame, row_idx: int, col_idx: int, max_rows: int = 4) -> Optional[str]:
    """Procura o primeiro valor não vazio abaixo da célula (row_idx, col_idx)"""
    for offset in range(1, max_rows + 1):
        if row_idx + offset < len(df):
            val = df.iloc[row_idx + offset, col_idx]
            if pd.notna(val) and str(val).strip() != '':
                s_val = str(val).strip()
                # Se parecer um rótulo de outro campo ou início de contrato, para a busca
                if s_val.endswith(':') or any(k in s_val for k in ['Contrato', 'Serviços', 'Vendedor:']):
                    break
                return s_val
    return None


def extract_contrato_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de contratos usando busca por contexto (rótulos e valores próximos)
    Suporta layouts multi-linha onde o valor fica abaixo do rótulo.
    """
    contratos = []
    contrato_atual = {}
    
    # Limpeza básica: remover colunas completamente vazias
    df = df.dropna(axis=1, how='all')
    
    for idx, row in df.iterrows():
        # Gerar uma string da linha inteira para detecção de triggers
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
        
        # Trigger: Início de um novo bloco de contrato
        if 'Contrato' in row_str and ('/' in row_str or '202' in row_str):
            # Salvar o contrato que estávamos processando
            if contrato_atual and 'numero_contrato' in contrato_atual:
                contratos.append(contrato_atual.copy())
            
            # Inicializar novo buffer de contrato
            contrato_atual = {'status': 'Ativo'} # Default
            
            # Extrair número e tipo (ex: "Contrato 000007/2023 - Locação")
            match = re.search(r'Contrato\s+([\d/]+)', row_str)
            if match:
                contrato_atual['numero_contrato'] = match.group(0).strip()
            else:
                contrato_atual['numero_contrato'] = row_str.split('-')[0].strip()
            
            if '-' in row_str:
                contrato_atual['tipo_contrato'] = row_str.split('-')[-1].strip()
            continue

        # Scan por rótulos nas células da linha atual
        for col_idx, cell_val in enumerate(row.values):
            if pd.isna(cell_val): continue
            label = str(cell_val).strip()
            
            if 'Cliente:' in label:
                contrato_atual['cliente'] = _find_value_below(df, idx, col_idx)
            
            elif 'Dia de Cobrança:' in label:
                contrato_atual['dia_cobranca'] = _find_value_below(df, idx, col_idx)
                
            elif 'Vigência:' in label:
                vig = _find_value_below(df, idx, col_idx)
                if vig:
                    if ' - ' in vig:
                        parts = vig.split(' - ')
                        contrato_atual['data_inicio'] = parts[0].strip()
                        contrato_atual['data_fim'] = parts[1].strip() if 'Indeterminado' not in parts[1] else None
                    else:
                        contrato_atual['data_inicio'] = vig.strip()
            
            elif 'Status:' in label:
                val = _find_value_below(df, idx, col_idx)
                if val: contrato_atual['status'] = val
                
            elif 'Valor' == label or 'Valor:' in label:
                # O valor costuma estar abaixo de "Valor"
                val = _find_value_below(df, idx, col_idx)
                if val:
                    num = detect_and_convert_currency(val)
                    if num: contrato_atual['valor_mensal'] = num
            
            elif 'Forma de Pagamento:' in label:
                contrato_atual['forma_pagamento'] = _find_value_below(df, idx, col_idx)
                
            elif 'Índice de Reajuste:' in label:
                contrato_atual['indice_reajuste'] = _find_value_below(df, idx, col_idx)
            
            elif 'Serv.' in label and 'Principal' in label:
                contrato_atual['servico_principal'] = _find_value_below(df, idx, col_idx)

    # Adicionar o último contrato do loop
    if contrato_atual and 'numero_contrato' in contrato_atual:
        contratos.append(contrato_atual)
    
    if not contratos:
        return pd.DataFrame()
        
    df_res = pd.DataFrame(contratos)
    
    # Converter colunas de data para formato ISO
    for col in ['data_inicio', 'data_fim']:
        if col in df_res.columns:
            df_res[col] = df_res[col].apply(detect_and_convert_date)
            
    return df_res


def parse_endereco(endereco_str: str) -> dict:
    """
    Parse de endereço brasileiro em componentes
    """
    if not endereco_str or endereco_str == 'Endereço não encontrado.':
        return {
            'logradouro': '',
            'numero': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'cep': ''
        }
    
    resultado = {
        'logradouro': '',
        'numero': '',
        'bairro': '',
        'cidade': '',
        'estado': '',
        'cep': ''
    }
    
    # Padrão: Rua Nome, 123 - Bairro, Cidade - UF, CEP
    import re
    
    # Extrair CEP (5 dígitos - 3 dígitos)
    cep_match = re.search(r'(\d{5})-?(\d{3})', endereco_str)
    if cep_match:
        resultado['cep'] = f"{cep_match.group(1)}-{cep_match.group(2)}"
    
    # Extrair UF (2 letras maiúsculas após hífen)
    uf_match = re.search(r'-\s*([A-Z]{2})\s*,', endereco_str)
    if uf_match:
        resultado['estado'] = uf_match.group(1)
    
    # Extrair Cidade (entre vírgula e -UF)
    cidade_match = re.search(r',\s*([^,]+)\s*-\s*[A-Z]{2}', endereco_str)
    if cidade_match:
        resultado['cidade'] = cidade_match.group(1).strip()
    
    # Extrair Bairro (entre - e ,cidade)
    bairro_match = re.search(r'-\s*([^,]+)\s*,\s*[^,]+\s*-\s*[A-Z]{2}', endereco_str)
    if bairro_match:
        resultado['bairro'] = bairro_match.group(1).strip()
    
    # Extrair Logradouro e Número (início até a primeira vírgula)
    primeira_parte = endereco_str.split(',')[0]
    numero_match = re.search(r',\s*(\d+|S/N|SN)\s*-', endereco_str)
    if numero_match:
        resultado['numero'] = numero_match.group(1)
        logradouro = primeira_parte.replace(f", {resultado['numero']}", '').strip()
        resultado['logradouro'] = logradouro
    else:
        resultado['logradouro'] = primeira_parte.strip()
    
    return resultado
