import json
import logging
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
    if request.method != 'POST':
        return JsonResponse({'success': False, 'detail': 'Metodo não permitido'}, status=405)
    
    try:
        file = request.FILES.get('file')
        module_type = request.POST.get('module_type')
        template_id = request.POST.get('template_id')
        
        if not file:
             return JsonResponse({'success': False, 'detail': 'Arquivo não enviado'}, status=400)
        
        if not FileService.validate_file(file.name):
            return JsonResponse({
                'success': False, 
                'detail': f'Tipo de arquivo não suportado. Use: {FileService.ALLOWED_EXTENSIONS}'
            }, status=400)
            
        # Salvar arquivo
        file_path = FileService.save_upload_file(file, file.name)
        
        # Analisar estrutura
        file_type = FileService.detect_file_type(file_path)
        analysis = FileService.analyze_structure(file_path, file_type)
        
        # Se tiver template_id, aplicar mapeamento
        if template_id and template_id.isdigit():
            import_service = ImportService()
            preview = import_service.get_import_preview(int(template_id), file_path)
            analysis["mapped_preview"] = preview
        else:
            # Sugerir mapeamento
            suggestions = TemplateService.suggest_mapping(
                [col["name"] for col in analysis["columns"]],
                module_type
            )
            analysis["mapping_suggestions"] = suggestions
            
        return JsonResponse({
            'success': True,
            'filename': file.name,
            'file_path': file_path,
            'module_type': module_type,
            'template_id': template_id,
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
        file_path = data.get('file_path')
        dry_run = data.get('dry_run', False)
        
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
