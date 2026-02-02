"""
Serviço para gerenciamento de templates de importação
"""
import json
import logging
from typing import List, Optional, Dict, Any
from django.utils import timezone
from ..models import ImportTemplate, ModuleField
from .ai_service import find_similar_columns

logger = logging.getLogger(__name__)


class TemplateService:
    """Serviço para CRUD de templates"""
    
    @staticmethod
    def create_template(
        name: str,
        module_type: str,
        mapping: Dict[str, str],
        column_types: Optional[Dict[str, str]] = None,
        file_type: str = "xlsx",
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_rows: int = 0,
        header_row: int = 0,
        description: Optional[str] = None
    ) -> ImportTemplate:
        """Cria novo template"""
        
        template = ImportTemplate.objects.create(
            name=name,
            module_type=module_type,
            mapping=mapping,
            column_types=column_types or {},
            file_type=file_type,
            delimiter=delimiter,
            encoding=encoding,
            skip_rows=skip_rows,
            header_row=header_row,
            description=description,
            is_active=True
        )
        
        logger.info(f"Template criado: {template.id} - {name}")
        return template
    
    @staticmethod
    def get_template(template_id: int) -> Optional[ImportTemplate]:
        """Busca template por ID"""
        try:
            return ImportTemplate.objects.get(id=template_id, is_active=True)
        except ImportTemplate.DoesNotExist:
            return None
    
    @staticmethod
    def get_templates(
        module_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTemplate]:
        """Lista templates com filtros opcionais"""
        query = ImportTemplate.objects.filter(is_active=True)
        
        if module_type:
            query = query.filter(module_type=module_type)
        
        return query.order_by('-created_at')[skip:skip+limit]
    
    @staticmethod
    def update_template(
        template_id: int,
        **kwargs
    ) -> Optional[ImportTemplate]:
        """Atualiza template"""
        template = TemplateService.get_template(template_id)
        if not template:
            return None
        
        # Campos permitidos
        allowed_fields = [
            'name', 'description', 'mapping', 'column_types',
            'file_type', 'delimiter', 'encoding', 'skip_rows', 'header_row'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(template, field):
                setattr(template, field, value)
        
        template.save()
        
        logger.info(f"Template atualizado: {template_id}")
        return template
    
    @staticmethod
    def delete_template(template_id: int) -> bool:
        """Soft delete de template"""
        template = TemplateService.get_template(template_id)
        if not template:
            return False
        
        template.is_active = False
        template.save()
        
        logger.info(f"Template deletado: {template_id}")
        return True
    
    @staticmethod
    def duplicate_template(template_id: int, new_name: Optional[str] = None) -> Optional[ImportTemplate]:
        """Duplica um template"""
        template = TemplateService.get_template(template_id)
        if not template:
            return None
        
        # Criar novo com mesmos dados
        new_template = ImportTemplate.objects.create(
            name=new_name or f"{template.name} (Cópia)",
            module_type=template.module_type,
            mapping=template.mapping.copy(),
            column_types=template.column_types.copy() if template.column_types else {},
            file_type=template.file_type,
            delimiter=template.delimiter,
            encoding=template.encoding,
            skip_rows=template.skip_rows,
            header_row=template.header_row,
            description=template.description,
            is_active=True
        )
        
        logger.info(f"Template duplicado: {template_id} -> {new_template.id}")
        return new_template
    
    @staticmethod
    def suggest_mapping(
        source_columns: List[str],
        module_type: str,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Sugere mapeamento de colunas baseado em similaridade
        """
        # Buscar campos do módulo
        module_fields = ModuleField.objects.filter(
            module_type=module_type,
            is_active=True
        )
        
        target_columns = [field.field_name for field in module_fields]
        target_labels = {field.field_name: field.field_label for field in module_fields}
        
        # Encontrar similaridades
        suggestions = find_similar_columns(source_columns, target_columns, threshold)
        
        # Adicionar informações dos campos
        detailed_suggestions = {}
        for source, target in suggestions.items():
            detailed_suggestions[source] = {
                "field": target,
                "label": target_labels.get(target, target),
                "confidence": "high"  # Poderíamos calcular score real aqui
            }
        
        # Campos não mapeados
        unmapped = [col for col in source_columns if col not in suggestions]
        
        return {
            "suggestions": detailed_suggestions,
            "unmapped_columns": unmapped,
            "available_fields": [
                {"name": f.field_name, "label": f.field_label, "type": f.field_type}
                for f in module_fields
            ]
        }
