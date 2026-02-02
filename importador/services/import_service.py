"""
Serviço para execução de importações
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from django.utils import timezone
import pandas as pd
from ..models import ImportJob, ImportStatus, ImportTemplate, ModuleField
from .file_service import FileService
from .ai_service import DataCleaningService

logger = logging.getLogger(__name__)


class ImportResult:
    """Resultado de uma importação"""
    def __init__(self):
        self.success = False
        self.message = ""
        self.total_rows = 0
        self.processed_rows = 0
        self.inserted_rows = 0
        self.updated_rows = 0
        self.error_rows = 0
        self.skipped_rows = 0
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.preview: List[Dict] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "inserted_rows": self.inserted_rows,
            "updated_rows": self.updated_rows,
            "error_rows": self.error_rows,
            "skipped_rows": self.skipped_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "preview": self.preview,
        }


class ImportService:
    """Serviço para executar importações"""
    
    def __init__(self):
        self.cleaning_service = DataCleaningService()
    
    def create_job(
        self,
        template_id: int,
        file_path: str,
        original_filename: str,
        dry_run: bool = False
    ) -> ImportJob:
        """Cria um novo job de importação"""
        template = ImportTemplate.objects.get(id=template_id)
        job = ImportJob.objects.create(
            template=template,
            filename=file_path,
            original_filename=original_filename,
            status=ImportStatus.PENDING,
            dry_run=dry_run,
            total_rows=0,
            processed_rows=0,
            error_rows=0
        )
        
        logger.info(f"Job criado: {job.id}")
        return job
    
    def get_job(self, job_id: int) -> Optional[ImportJob]:
        """Busca job por ID"""
        try:
            return ImportJob.objects.get(id=job_id)
        except ImportJob.DoesNotExist:
            return None
    
    def execute_import(
        self,
        job_id: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ImportResult:
        """
        Executa importação de um job
        """
        job = self.get_job(job_id)
        if not job:
            result = ImportResult()
            result.message = f"Job {job_id} não encontrado"
            return result
        
        template = job.template
        if not template:
            result = ImportResult()
            result.message = f"Template do job {job_id} não encontrado"
            job.update_status(ImportStatus.ERROR)
            return result
        
        result = ImportResult()
        
        try:
            # Atualizar status
            job.update_status(ImportStatus.PROCESSING)
            
            # Ler arquivo
            logger.info(f"Lendo arquivo: {job.filename}")
            file_type = FileService.detect_file_type(job.filename)
            
            df = FileService.read_file(
                job.filename,
                file_type=file_type,
                header_row=template.header_row,
                skip_rows=template.skip_rows
            )
            
            result.total_rows = len(df)
            job.total_rows = result.total_rows
            job.save()
            
            # Limpar dados
            logger.info("Limpando e padronizando dados...")
            df_clean, clean_report = self.cleaning_service.clean(
                df,
                column_types=template.column_types
            )
            
            # Aplicar mapeamento
            logger.info("Aplicando mapeamento de colunas...")
            df_mapped = self._apply_mapping(df_clean, template.mapping)
            
            # Validar dados
            logger.info("Validando dados...")
            validation_result = self._validate_data(df_mapped, template.module_type)
            
            # Preview (primeiros 5 registros)
            # Converter tipos não serializáveis (como as datas do pandas) para string
            df_preview = df_mapped.head(5).copy()
            for col in df_preview.columns:
                if df_preview[col].dtype == 'datetime64[ns]':
                    df_preview[col] = df_preview[col].dt.strftime('%Y-%m-%d')
            result.preview = df_preview.to_dict('records')
            
            # Se for dry_run, apenas simular
            if job.dry_run:
                result.success = True
                result.message = "Simulação concluída (dry_run=True)"
                result.processed_rows = result.total_rows
                job.update_status(ImportStatus.COMPLETED)
                return result
            
            # Importar dados
            logger.info("Importando dados para o banco...")
            insert_count = self._import_data(df_mapped, template.module_type, job, progress_callback)
            
            result.success = True
            result.message = "Importação concluída com sucesso"
            result.processed_rows = result.total_rows
            result.inserted_rows = insert_count
            
            job.inserted_rows = insert_count
            job.update_status(ImportStatus.COMPLETED)
            
            logger.info(f"Importação concluída: {insert_count} registros inseridos")
            
        except Exception as e:
            logger.error(f"Erro na importação: {e}", exc_info=True)
            result.message = f"Erro na importação: {str(e)}"
            job.update_status(ImportStatus.ERROR)
        
        return result
    
    def _apply_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Aplica mapeamento de colunas
        Renomeia colunas da planilha para nomes dos campos do sistema
        """
        # mapping is {source_column: target_field}
        # We want a DataFrame where the columns are the target_field names.
        
        # Create a dictionary for renaming
        rename_dict = mapping
        
        # Subset current columns that are in the mapping
        available_cols = [col for col in df.columns if col in mapping]
        
        # Filter and rename
        df_mapped = df[available_cols].rename(columns=rename_dict)
        
        return df_mapped
    
    def _validate_data(
        self,
        df: pd.DataFrame,
        module_type: str
    ) -> Dict[str, Any]:
        """
        Valida dados antes de importar
        """
        # Buscar campos obrigatórios do módulo
        required_fields = ModuleField.objects.filter(
            module_type=module_type,
            required=True,
            is_active=True
        )
        
        errors = []
        warnings = []
        
        for field in required_fields:
            if field.field_name not in df.columns:
                errors.append(f"Campo obrigatório não mapeado: {field.field_name}")
            else:
                # Verificar valores vazios
                empty_count = df[field.field_name].isna().sum()
                if empty_count > 0:
                    warnings.append(f"Campo {field.field_name} tem {empty_count} valores vazios")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _import_data(
        self,
        df: pd.DataFrame,
        module_type: str,
        job: ImportJob,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Importa dados para o banco
        Retorna quantidade de registros inseridos
        """
        # Importar processadores específicos
        from .ai_service import extract_cliente_data, extract_contrato_data
        
        inserted = 0
        
        # Processar conforme o tipo de módulo
        if module_type == 'clientes':
            # Usar extrator específico para clientes
            df_processed = extract_cliente_data(df)
        elif module_type == 'contratos':
            # Usar extrator específico para contratos
            df_processed = extract_contrato_data(df)
        else:
            df_processed = df
        
        # Se o DataFrame processado estiver vazio, retornar 0
        if df_processed.empty:
            return 0
            
        # Aqui você implementaria a lógica real de inserção no seu ERP
        # Por enquanto, apenas simulamos
        
        total_rows = len(df_processed)
        for idx, row in df_processed.iterrows():
            try:
                # Simular inserção
                # TODO: Substituir pela inserção real no seu ERP
                
                inserted += 1
                job.processed_rows = inserted
                
                # Callback de progresso
                if progress_callback:
                    progress_callback(inserted, total_rows)
                
                # Commit a cada 100 registros (se estivesse usando uma sessão real do banco)
                # if inserted % 100 == 0:
                #    self.db.commit()
                    
            except Exception as e:
                job.error_rows += 1
                ImportError.objects.create(
                    job=job,
                    row_number=idx + 1,
                    error_type="general",
                    message=str(e),
                    raw_data=row.to_dict()
                )
        
        job.save()
        return inserted
    
    def get_import_preview(
        self,
        template_id: int,
        file_path: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retorna preview de como os dados ficarão após importação
        """
        try:
            template = ImportTemplate.objects.get(id=template_id)
        except ImportTemplate.DoesNotExist:
            return {"error": "Template não encontrado"}
        
        try:
            # Ler arquivo
            file_type = FileService.detect_file_type(file_path)
            df = FileService.read_file(
                file_path, 
                file_type=file_type,
                header_row=template.header_row,
                skip_rows=template.skip_rows
            )
            
            # Limpar
            df_clean, _ = self.cleaning_service.clean(df, template.column_types)
            
            # Aplicar mapeamento
            df_mapped = self._apply_mapping(df_clean, template.mapping)
            
            # Converter tipos para preview serializável
            df_preview = df_mapped.head(limit).copy()
            for col in df_preview.columns:
                if df_preview[col].dtype == 'datetime64[ns]':
                    df_preview[col] = df_preview[col].dt.strftime('%Y-%m-%d')
            
            return {
                "columns": list(df_mapped.columns),
                "preview": df_preview.to_dict('records'),
                "total_rows": len(df_mapped),
                "mapping_applied": template.mapping
            }
            
        except Exception as e:
            logger.error(f"Erro no preview: {e}", exc_info=True)
            return {"error": str(e)}
    
    def cancel_job(self, job_id: int) -> bool:
        """Cancela um job pendente"""
        job = self.get_job(job_id)
        if not job or job.status != ImportStatus.PENDING:
            return False
        
        job.update_status(ImportStatus.CANCELLED)
        return True
