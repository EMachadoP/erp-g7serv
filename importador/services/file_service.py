"""
Serviço para leitura e manipulação de arquivos Excel/CSV
"""
import os
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import chardet

import pandas as pd
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger(__name__)


class FileService:
    """Serviço para manipulação de arquivos"""
    
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB default
    
    @staticmethod
    def validate_file(filename: str) -> bool:
        """Valida se arquivo tem extensão permitida constellations"""
        ext = Path(filename).suffix.lower()
        return ext in FileService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def detect_file_type(filepath: str) -> str:
        """Detecta tipo de arquivo baseado na extensão"""
        ext = Path(filepath).suffix.lower()
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {ext}")
    
    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """Detecta encoding de arquivo"""
        result = chardet.detect(file_content)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        
        logger.info(f"Encoding detectado: {encoding} (confiança: {confidence:.2%})")
        
        # Fallback para utf-8 se confiança for baixa (ou se for windows-1252/iso-8859-1 que é comum em planilhas BR)
        if confidence < 0.7:
             return 'latin-1' # Better default for Brazilian spreadsheets if unsure
        
        return encoding
    
    @staticmethod
    def detect_csv_delimiter(file_content: str) -> str:
        """Detecta delimitador de CSV"""
        sample = file_content[:4096]
        
        # Contar ocorrências de delimitadores comuns
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample.count(d) for d in delimiters}
        
        # Escolher o mais comum
        best_delimiter = max(counts, key=counts.get)
        
        logger.info(f"Delimitador detectado: '{best_delimiter}' (contagem: {counts[best_delimiter]})")
        
        return best_delimiter
    
    @staticmethod
    def save_upload_file(file_obj, filename: str) -> str:
        """Salva arquivo de upload usando o storage do Django"""
        path = default_storage.save(f'uploads/imports/{filename}', ContentFile(file_obj.read()))
        full_path = default_storage.path(path)
        logger.info(f"Arquivo salvo: {full_path}")
        return full_path
    
    @staticmethod
    def read_excel(
        filepath: str,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
        skip_rows: int = 0
    ) -> pd.DataFrame:
        """
        Lê arquivo Excel e retorna DataFrame
        """
        try:
            # Se não especificar aba, ler a primeira
            if sheet_name is None:
                xl = pd.ExcelFile(filepath)
                sheet_name = xl.sheet_names[0]
            
            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                header=header_row,
                skiprows=skip_rows
            )
            
            # Limpeza básica do DataFrame
            df = FileService.clean_dataframe(df)
            
            logger.info(f"Excel lido: {filepath}, aba: {sheet_name}, linhas: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler Excel {filepath}: {e}")
            raise
    
    @staticmethod
    def read_csv(
        filepath: str,
        delimiter: Optional[str] = None,
        encoding: Optional[str] = None,
        header_row: int = 0,
        skip_rows: int = 0
    ) -> pd.DataFrame:
        """
        Lê arquivo CSV e retorna DataFrame
        """
        try:
            # Ler conteúdo bruto para detectar encoding e delimitador
            with open(filepath, 'rb') as f:
                raw_content = f.read()
            
            # Detectar encoding
            if encoding is None:
                encoding = FileService.detect_encoding(raw_content)
            
            # Decodificar
            try:
                content = raw_content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback final
                content = raw_content.decode('latin-1', errors='replace')
            
            # Detectar delimitador
            if delimiter is None:
                delimiter = FileService.detect_csv_delimiter(content)
            
            # Criar DataFrame
            df = pd.read_csv(
                io.StringIO(content),
                delimiter=delimiter,
                header=header_row,
                skiprows=skip_rows,
                engine='python'
            )
            
            # Limpeza básica do DataFrame
            df = FileService.clean_dataframe(df)
            
            logger.info(f"CSV lido: {filepath}, encoding: {encoding}, delimiter: '{delimiter}', linhas: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler CSV {filepath}: {e}")
            raise
    
    @staticmethod
    def read_file(
        filepath: str,
        file_type: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Lê qualquer arquivo suportado (Excel ou CSV)
        """
        if file_type is None:
            file_type = FileService.detect_file_type(filepath)
        
        if file_type == 'excel':
            return FileService.read_excel(filepath, **kwargs)
        elif file_type == 'csv':
            return FileService.read_csv(filepath, **kwargs)
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
    
    @staticmethod
    def get_excel_sheets(filepath: str) -> List[str]:
        """Retorna lista de abas de um arquivo Excel"""
        try:
            xl = pd.ExcelFile(filepath)
            return xl.sheet_names
        except Exception as e:
            logger.error(f"Erro ao ler abas do Excel {filepath}: {e}")
            return []
    
    @staticmethod
    def analyze_structure(filepath: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa estrutura do arquivo e retorna metadados
        """
        if file_type is None:
            file_type = FileService.detect_file_type(filepath)
        
        result = {
            "file_type": file_type,
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "sheets": [],
            "columns": [],
            "preview": [],
            "row_count": 0
        }
        
        try:
            if file_type == 'excel':
                # Analisar Excel
                result["sheets"] = FileService.get_excel_sheets(filepath)
                
                # Ler primeira aba para análise
                df = FileService.read_excel(filepath)
                
            else:
                # Analisar CSV
                df = FileService.read_csv(filepath)
            
            # Informações das colunas
            result["columns"] = [
                {
                    "name": str(col),
                    "dtype": str(df[col].dtype),
                    "sample_values": df[col].dropna().head(3).tolist()
                }
                for col in df.columns
            ]
            
            # Preview dos dados (primeiras 5 linhas)
            # Converter tipos não serializáveis (como as datas do pandas) para string
            df_preview = df.head(5).copy()
            for col in df_preview.columns:
                if df_preview[col].dtype == 'datetime64[ns]':
                    df_preview[col] = df_preview[col].dt.strftime('%Y-%m-%d')
            
            result["preview"] = df_preview.to_dict('records')
            
            # Contagem de linhas
            result["row_count"] = len(df)
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Erro ao analisar arquivo {filepath}: {e}")
        
        return result
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa DataFrame básico"""
        # Remover colunas completamente vazias
        df = df.dropna(axis=1, how='all')
        
        # Remover linhas completamente vazias
        df = df.dropna(axis=0, how='all')
        
        # Limpar nomes de colunas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Resetar índice
        df = df.reset_index(drop=True)
        
        return df
