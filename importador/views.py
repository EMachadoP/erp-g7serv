import json
import logging
import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage

from .models import ImportTemplate, ImportJob, ImportStatus, ModuleField
from .services import FileService, TemplateService, ImportService

logger = logging.getLogger(__name__)

# --- UI Views ---

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'importador/index.html'

class UploadPageView(LoginRequiredMixin, TemplateView):
    template_name = 'importador/upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = TemplateService.get_templates()
        return context

class TemplatesPageView(LoginRequiredMixin, ListView):
    model = ImportTemplate
    template_name = 'importador/templates.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        return ImportTemplate.objects.filter(is_active=True).order_by('-created_at')

class TemplateEditPageView(LoginRequiredMixin, DetailView):
    model = ImportTemplate
    template_name = 'importador/template_edit.html'
    context_object_name = 'template'
    
    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        if pk == 0:  # Use 0 or similar for "new" if needed, or handle separately
            return None
        return super().get_object(queryset)

class ImportHistoryPageView(LoginRequiredMixin, ListView):
    model = ImportJob
    template_name = 'importador/importacoes.html'
    context_object_name = 'jobs'
    ordering = ['-created_at']

class ImportDetailPageView(LoginRequiredMixin, DetailView):
    model = ImportJob
    template_name = 'importador/importacao_detail.html'
    context_object_name = 'job'

# --- API Endpoints ---

@csrf_exempt # For simplicity in dev, ideally keep CSRF if called from same domain
def api_upload_file(request):
    """
    API para upload de arquivo e análise inicial
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'detail': 'Método não permitido'}, status=405)
    
    try:
        file = request.FILES.get('file')
        module_type = request.POST.get('module_type')
        template_id = request.POST.get('template_id')
        
        if not file or not module_type:
            return JsonResponse({'success': False, 'detail': 'Arquivo e tipo de módulo são obrigatórios'}, status=400)
            
        file_service = FileService()
        if not file_service.validate_file(file.name):
            return JsonResponse({'success': False, 'detail': 'Tipo de arquivo não suportado'}, status=400)
            
        # Salvar arquivo temporariamente
        file_path = file_service.save_upload_file(file, file.name)
        
        # Analisar estrutura
        file_type = file_service.detect_file_type(file_path)
        analysis = file_service.analyze_structure(file_path, file_type)
        
        # Se for clientes ou contratos, usar processamento especial
        if module_type == 'clientes':
            from .services.ai_service import extract_cliente_data
            
            df = file_service.read_file(file_path, file_type=file_type)
            df_clientes = extract_cliente_data(df)
            
            # Função para limpar qualquer valor NaN de forma segura
            def clean_value(val):
                try:
                    if val is None:
                        return ""
                    if pd.isna(val):
                        return ""
                    # Converter para string para garantir serialização
                    return str(val)
                except (TypeError, ValueError):
                    return ""
            
            # Converter DataFrame para lista de dicts com limpeza robusta
            preview_data = []
            for _, row in df_clientes.head(10).iterrows():
                clean_row = {col: clean_value(val) for col, val in row.items()}
                preview_data.append(clean_row)
            
            return JsonResponse({
                "success": True,
                "filename": file.name,
                "file_path": file_path,
                "module_type": module_type,
                "special_processing": True,
                "preview_type": "clientes",
                "total": len(df_clientes),
                "preview": preview_data,
                "columns": list(df_clientes.columns) if not df_clientes.empty else [],
                "analysis": analysis
            })
        
        elif module_type == 'contratos':
            from .services.ai_service import extract_contrato_data
            df = file_service.read_file(file_path, file_type=file_type)
            df_contratos = extract_contrato_data(df)
            
            # Limpar NaN para evitar erro de JSON
            df_json = df_contratos.where(df_contratos.notnull(), None)
            
            return JsonResponse({
                "success": True,
                "filename": file.name,
                "file_path": file_path,
                "module_type": module_type,
                "special_processing": True,
                "preview_type": "contratos",
                "total": len(df_contratos),
                "preview": df_json.head(10).to_dict('records') if not df_json.empty else [],
                "columns": list(df_contratos.columns) if not df_contratos.empty else [],
                "analysis": analysis
            })
        
        # Fluxo normal
        template_service = TemplateService()
        if template_id:
            # Aplicar mapeamento do template
            import_service = ImportService()
            # Ensure template_id is an int if it's a string
            template_id_int = int(template_id) if isinstance(template_id, str) and template_id.isdigit() else None
            if template_id_int is not None:
                preview = import_service.get_import_preview(template_id_int, file_path)
                analysis['mapped_preview'] = preview
            else:
                # Handle case where template_id is provided but not a valid digit
                logger.warning(f"Invalid template_id received: {template_id}")
                # Fallback to suggestions if template_id is invalid
                suggestions = template_service.suggest_mapping(
                    [col['name'] for col in analysis['columns']], 
                    module_type
                )
                analysis['mapping_suggestions'] = suggestions
        else:
            # Sugerir mapeamento
            suggestions = template_service.suggest_mapping(
                [col['name'] for col in analysis['columns']], 
                module_type
            )
            analysis['mapping_suggestions'] = suggestions
            
        return JsonResponse({
            'success': True,
            'filename': file.name,
            'file_path': file_path,
            'module_type': module_type,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Erro no upload: {e}", exc_info=True)
        return JsonResponse({'success': False, 'detail': str(e)}, status=500)

def api_get_module_fields(request, module_type):
    fields = ModuleField.objects.filter(module_type=module_type, is_active=True).order_by('order')
    return JsonResponse({
        'success': True,
        'module_type': module_type,
        'fields': [f.to_dict() for f in fields]
    })

@method_decorator(csrf_exempt, name='dispatch')
class TemplateListCreateAPI(View):
    def get(self, request):
        module_type = request.GET.get('module_type')
        templates = TemplateService.get_templates(module_type=module_type)
        return JsonResponse({
            'success': True,
            'templates': [
                {
                    'id': t.id,
                    'name': t.name,
                    'module_type': t.module_type,
                    'mapping_count': len(t.mapping),
                    'created_at': t.created_at.isoformat(),
                    'updated_at': t.updated_at.isoformat()
                } for t in templates
            ]
        })
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            template = TemplateService.create_template(**data)
            return JsonResponse({
                'success': True,
                'message': 'Template criado com sucesso',
                'template': {'id': template.id, 'name': template.name}
            })
        except Exception as e:
            return JsonResponse({'success': False, 'detail': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class TemplateDetailAPI(View):
    def get(self, request, pk):
        template = TemplateService.get_template(pk)
        if not template:
            return JsonResponse({'success': False, 'detail': 'Não encontrado'}, status=404)
        return JsonResponse({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'module_type': template.module_type,
                'mapping': template.mapping,
                'column_types': template.column_types,
                'description': template.description
            }
        })
    
    def put(self, request, pk):
        try:
            data = json.loads(request.body)
            template = TemplateService.update_template(pk, **data)
            if not template:
                return JsonResponse({'success': False, 'detail': 'Não encontrado'}, status=404)
            return JsonResponse({'success': True, 'message': 'Atualizado'})
        except Exception as e:
            return JsonResponse({'success': False, 'detail': str(e)}, status=400)
    
    def delete(self, request, pk):
        success = TemplateService.delete_template(pk)
        return JsonResponse({'success': success})

@csrf_exempt
def api_execute_import(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        module_type = data.get('module_type') # Novo: suporte a módulo direto
        file_path = data.get('file_path')
        dry_run = data.get('dry_run', False)
        
        # Se for um módulo especializado e não tiver template, buscar/criar um padrão
        if not template_id and module_type in ['clientes', 'contratos', 'orcamentos']:
            template, created = ImportTemplate.objects.get_or_create(
                module_type=module_type,
                name=f"Template Sistema - {module_type.capitalize()}",
                defaults={
                    'mapping': {}, # Mapeamento vazio pq o serviço especializado cuida disso
                    'description': 'Template gerado automaticamente pelo sistema para o importador inteligente.'
                }
            )
            template_id = template.id
            
        import_service = ImportService()
        job = import_service.create_job(
            template_id=template_id,
            file_path=file_path,
            original_filename=file_path.split("/")[-1],
            dry_run=dry_run
        )
        
        # Execute (ideally background, but for now blocking to see results)
        result = import_service.execute_import(job.id)
        
        return JsonResponse({
            'success': result.success,
            'message': result.message,
            'job_id': job.id,
            'result': result.to_dict()
        })
    except Exception as e:
        logger.error(f"Erro na importação: {e}", exc_info=True)
        return JsonResponse({'success': False, 'detail': str(e)}, status=500)

@csrf_exempt
def api_import_preview(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        file_path = data.get('file_path')
        
        import_service = ImportService()
        preview = import_service.get_import_preview(template_id, file_path)
        
        if "error" in preview:
            return JsonResponse({'success': False, 'detail': preview["error"]}, status=400)
            
        return JsonResponse({
            'success': True,
            'preview': preview
        })
    except Exception as e:
        return JsonResponse({'success': False, 'detail': str(e)}, status=500)

def api_list_jobs(request):
    template_id = request.GET.get('template_id')
    status = request.GET.get('status')
    
    query = ImportJob.objects.all()
    if template_id:
        query = query.filter(template_id=template_id)
    if status:
        query = query.filter(status=status)
        
    jobs = query.order_by('-created_at')[:100]
    
    return JsonResponse({
        'success': True,
        'jobs': [
            {
                'id': j.id,
                'filename': j.original_filename,
                'template_name': j.template.name if j.template else None,
                'status': j.status,
                'progress': j.get_progress_percentage(),
                'total_rows': j.total_rows,
                'processed_rows': j.processed_rows,
                'error_rows': j.error_rows,
                'created_at': j.created_at.isoformat()
            } for j in jobs
        ]
    })
