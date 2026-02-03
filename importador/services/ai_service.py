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
    Extrai dados de clientes de planilhas.
    Detecta automaticamente se a planilha é:
    1. Tabular (com headers de coluna como Nome, CPF, Telefone, etc.)
    2. Hierárquica (com prefixos como "CPF/CNPJ:", "Telefone:", etc.)
    """
    # Palavras que indicam headers/labels e não devem ser nomes
    LABELS_INVALIDOS = {
        'nome', 'cpf', 'cnpj', 'cpf/cnpj', 'telefone', 'fone', 'celular',
        'endereco', 'endereço', 'status', 'email', 'e-mail', 'contato',
        'rg', 'ie', 'inscrição', 'inscricao', 'razao', 'razão', 'fantasia',
        'cliente', 'clientes', '-', 'n/a', 'null', 'none', ''
    }
    
    def is_invalid_name(val):
        """Verifica se o valor é um label/header e não um nome válido"""
        if pd.isna(val):
            return True
        s = str(val).strip().lower()
        # Verifica se é um label conhecido
        if s in LABELS_INVALIDOS:
            return True
        # Verifica se parece um header (ex: "Nome:", "Telefone")
        if s.endswith(':'):
            return True
        # Muito curto para ser nome (menos de 2 caracteres)
        if len(s) < 2:
            return True
        # Verifica se parece um telefone (começa com ( ou tem formato de telefone)
        if s.startswith('(') or (len(s) >= 8 and s.replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit()):
            return True
        # Verifica se é só hífen ou traço
        if s in ['-', '–', '—']:
            return True
        return False
    
    def detect_format(df: pd.DataFrame) -> str:
        """Detecta se a planilha é tabular ou hierárquica"""
        # Verifica as primeiras linhas para detectar padrão
        first_rows = df.head(5)
        
        # Checar se primeira linha parece header
        first_row_str = ' '.join([str(v).lower() for v in first_rows.iloc[0].values if pd.notna(v)])
        has_header_keywords = any(kw in first_row_str for kw in ['nome', 'cpf', 'cnpj', 'telefone', 'endereço', 'endereco', 'status'])
        
        # Checar se existem prefixos hierárquicos
        all_text = ' '.join([str(v) for row in first_rows.values for v in row if pd.notna(v)])
        has_hierarchical_prefixes = any(prefix in all_text for prefix in ['CPF/CNPJ:', 'Telefone:', 'Endereço:', 'RG/Inscrição'])
        
        if has_hierarchical_prefixes:
            return 'hierarchical'
        elif has_header_keywords:
            return 'tabular'
        else:
            # Default: tentar tabular
            return 'tabular'
    
    def extract_tabular(df: pd.DataFrame) -> pd.DataFrame:
        """Extrai dados de planilha tabular (com colunas)"""
        # Mapear colunas por similaridade de nomes
        column_mapping = {}
        target_fields = {
            'nome': ['nome', 'razao', 'razão', 'cliente', 'nome cliente', 'razao social', 'razão social', 'name'],
            'cpf_cnpj': ['cpf', 'cnpj', 'cpf/cnpj', 'cpf_cnpj', 'documento', 'doc'],
            'telefone': ['telefone', 'fone', 'celular', 'tel', 'phone', 'contato'],
            'endereco': ['endereco', 'endereço', 'address', 'logradouro'],
            'status': ['status', 'situacao', 'situação', 'ativo'],
            'email': ['email', 'e-mail', 'mail'],
            'rg_ie': ['rg', 'ie', 'inscricao', 'inscrição', 'rg/ie'],
        }
        
        # Normalizar nomes das colunas
        col_names = [str(c).lower().strip() for c in df.columns]
        
        for target, aliases in target_fields.items():
            for idx, col_name in enumerate(col_names):
                if any(alias in col_name for alias in aliases):
                    column_mapping[target] = df.columns[idx]
                    break
        
        # Se não encontrou header na primeira linha, tentar usar a primeira linha como header
        if not column_mapping:
            # Verificar se a primeira linha contém headers
            first_row = df.iloc[0]
            potential_headers = [str(v).lower().strip() for v in first_row.values if pd.notna(v)]
            
            if any(any(alias in h for alias in aliases) for h, (target, aliases) in zip(potential_headers, target_fields.items())):
                # Usar primeira linha como header
                new_headers = [str(v).strip() if pd.notna(v) else f'col_{i}' for i, v in enumerate(first_row.values)]
                df = df.iloc[1:].copy()
                df.columns = new_headers[:len(df.columns)]
                
                # Refazer mapeamento
                col_names = [str(c).lower().strip() for c in df.columns]
                for target, aliases in target_fields.items():
                    for idx, col_name in enumerate(col_names):
                        if any(alias in col_name for alias in aliases):
                            column_mapping[target] = df.columns[idx]
                            break
        
        if not column_mapping:
            logger.warning("Não foi possível mapear colunas da planilha tabular")
            return pd.DataFrame()
        
        # Extrair dados
        clientes = []
        for idx, row in df.iterrows():
            cliente = {}
            
            for target, col in column_mapping.items():
                try:
                    val = row[col]
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if val_str and val_str.lower() not in LABELS_INVALIDOS:
                            cliente[target] = val_str
                except (KeyError, IndexError):
                    continue
            
            # Só adicionar se tiver nome válido ou CPF/CNPJ
            if cliente.get('nome') and not is_invalid_name(cliente['nome']):
                clientes.append(cliente)
            elif cliente.get('cpf_cnpj'):
                # Se não tem nome mas tem CPF/CNPJ, ainda assim incluir
                clientes.append(cliente)
        
        return pd.DataFrame(clientes) if clientes else pd.DataFrame()
    
    def extract_hierarchical(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrai dados de planilha com prefixos como 'CPF/CNPJ:'.
        Trata cada linha que contém CPF/CNPJ como um cliente individual.
        Também busca dados complementares nas linhas seguintes.
        """
        clientes = []
        processed_indices = set()  # Rastrear linhas já processadas
        
        for idx, row in df.iterrows():
            if idx in processed_indices:
                continue
                
            row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
            
            # Só processar linhas que têm CPF/CNPJ
            if 'CPF/CNPJ:' not in row_str:
                continue
            
            cliente = {}
            processed_indices.add(idx)
            
            # Extrair CPF/CNPJ da linha
            for val in row.values:
                if pd.notna(val) and 'CPF/CNPJ:' in str(val):
                    cpf_cnpj = str(val).split('CPF/CNPJ:')[1].strip()
                    cliente['cpf_cnpj'] = cpf_cnpj
                    break
            
            # Tentar extrair nome da primeira coluna (se não for inválido)
            if len(row) > 0 and pd.notna(row.iloc[0]):
                nome_candidato = str(row.iloc[0]).strip()
                if nome_candidato and not is_invalid_name(nome_candidato):
                    cliente['nome'] = nome_candidato
            
            # Extrair telefone se presente na linha atual
            for val in row.values:
                if pd.notna(val):
                    val_str = str(val).strip()
                    # Detectar telefone pelo formato brasileiro
                    if val_str.startswith('(') and len(val_str) >= 10:
                        cliente['telefone'] = val_str
                        break
                    # Formato com Telefone: prefixo
                    if 'Telefone:' in val_str:
                        tel = val_str.split('Telefone:')[1].strip()
                        if tel and tel != '-':
                            cliente['telefone'] = tel
                        break
            
            # Extrair endereço se presente na linha atual
            for val in row.values:
                if pd.notna(val) and 'Endereço:' in str(val):
                    endereco = str(val).split('Endereço:')[1].strip()
                    if endereco and endereco != 'Endereço não encontrado.':
                        cliente['endereco'] = endereco
                    break
            
            # Extrair Status
            for val in row.values:
                if pd.notna(val) and str(val).strip() in ['ATIVO', 'INATIVO']:
                    cliente['status'] = str(val).strip()
                    break
            
            # ========================================
            # Buscar dados complementares nas próximas 5 linhas
            # ========================================
            for offset in range(1, 6):
                next_idx = idx + offset
                if next_idx >= len(df):
                    break
                    
                next_row = df.iloc[next_idx]
                next_row_str = ' '.join([str(v) for v in next_row.values if pd.notna(v)])
                
                # Se encontrar outro CPF/CNPJ, parar (próximo cliente)
                if 'CPF/CNPJ:' in next_row_str:
                    break
                
                # Marcar como processada
                processed_indices.add(next_idx)
                
                # Buscar telefone se ainda não tem
                if 'telefone' not in cliente and 'Telefone:' in next_row_str:
                    for val in next_row.values:
                        if pd.notna(val) and 'Telefone:' in str(val):
                            tel = str(val).split('Telefone:')[1].strip()
                            if tel and tel != '-':
                                cliente['telefone'] = tel
                            break
                
                # Buscar endereço se ainda não tem
                if 'endereco' not in cliente and 'Endereço:' in next_row_str:
                    for val in next_row.values:
                        if pd.notna(val) and 'Endereço:' in str(val):
                            endereco = str(val).split('Endereço:')[1].strip()
                            if endereco and endereco != 'Endereço não encontrado.':
                                cliente['endereco'] = endereco
                            break
                
                # Buscar RG/IE se ainda não tem
                if 'rg_ie' not in cliente and 'RG/Inscrição' in next_row_str:
                    for val in next_row.values:
                        if pd.notna(val) and 'RG/Inscrição' in str(val):
                            rg_ie_parts = str(val).split(':')
                            if len(rg_ie_parts) > 1:
                                cliente['rg_ie'] = rg_ie_parts[1].strip()
                            break
            
            # Só adicionar se tiver ao menos CPF/CNPJ
            if cliente.get('cpf_cnpj'):
                clientes.append(cliente)
        
        return pd.DataFrame(clientes) if clientes else pd.DataFrame()
    
    # Detectar formato e extrair
    formato = detect_format(df)
    logger.info(f"Formato detectado para extração de clientes: {formato}")
    
    if formato == 'tabular':
        df_clientes = extract_tabular(df)
    else:
        df_clientes = extract_hierarchical(df)
    
    # Limpar CPF/CNPJ - remover prefixo e formatar
    if not df_clientes.empty and 'cpf_cnpj' in df_clientes.columns:
        def clean_cpf_cnpj(x):
            if pd.isna(x):
                return x
            s = str(x).strip()
            # Remover prefixo 'CPF/CNPJ:' se existir
            if 'CPF/CNPJ:' in s:
                s = s.split('CPF/CNPJ:')[1].strip()
            # Remover caracteres de formatação para contar dígitos
            digits_only = s.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')
            if len(digits_only) == 14:
                return detect_and_convert_cnpj(s)
            elif len(digits_only) == 11:
                return detect_and_convert_cpf(s)
            return s
        
        df_clientes['cpf_cnpj'] = df_clientes['cpf_cnpj'].apply(clean_cpf_cnpj)
    
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
