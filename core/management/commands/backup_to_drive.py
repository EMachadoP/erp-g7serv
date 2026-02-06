import os
import gzip
import shutil
import tempfile
import subprocess
from datetime import datetime
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class Command(BaseCommand):
    help = 'Executa backup do banco de dados e envia para o Google Drive'

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', help='Executa em modo de teste')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando processo de backup...'))
        
        # 1. Obter credenciais do banco
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            self.stdout.write(self.style.ERROR('DATABASE_URL não configurada.'))
            return

        url = urlparse(db_url)
        db_name = url.path[1:]
        db_user = url.username
        db_password = url.password
        db_host = url.hostname
        db_port = url.port or 5432

        # 2. Configurar ambiente para pg_dump
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password

        # 3. Gerar nome do arquivo
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_erp_{timestamp}.sql'
        compressed_filename = f'{filename}.gz'
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        compressed_path = os.path.join(temp_dir, compressed_filename)

        try:
            # 4. Executar pg_dump
            self.stdout.write(f'Executando pg_dump para {db_name}...')
            dump_cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-F', 'p',  # Plain text
                '-b',       # Include blobs
                '-v',       # Verbose
                '-f', file_path,
                db_name
            ]
            
            subprocess.run(dump_cmd, env=env, check=True, capture_output=True)

            # 5. Compactar
            self.stdout.write('Compactando arquivo...')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 6. Enviar para o Google Drive
            self.upload_to_drive(compressed_path, compressed_filename)

            self.stdout.write(self.style.SUCCESS(f'Backup concluído com sucesso: {compressed_filename}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante o backup: {str(e)}'))
            if hasattr(e, 'stderr'):
                self.stdout.write(self.style.ERROR(f'Detalhes: {e.stderr.decode()}'))
        finally:
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(compressed_path):
                os.remove(compressed_path)

    def upload_to_drive(self, file_path, filename):
        service_account_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON_PATH')
        # Alternativamente, podemos ler direto da variável de ambiente se for o conteúdo do JSON
        service_account_info_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

        if not folder_id:
            raise Exception('GOOGLE_DRIVE_FOLDER_ID não configurado.')

        # Auth
        if service_account_info_json:
            import json
            info = json.loads(service_account_info_json)
            creds = service_account.Credentials.from_service_account_info(info)
        elif service_account_path and os.path.exists(service_account_path):
            creds = service_account.Credentials.from_service_account_file(service_account_path)
        else:
            raise Exception('Credenciais do Google Drive não encontradas (GOOGLE_SERVICE_ACCOUNT_JSON).')

        creds = creds.with_scopes(['https://www.googleapis.com/auth/drive.file'])
        service = build('drive', 'v3', credentials=creds)

        # Upload
        self.stdout.write(f'Enviando {filename} para o Google Drive...')
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/gzip', resumable=True)
        
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                self.stdout.write(f'Progresso: {int(status.progress() * 100)}%')

        self.stdout.write(f'Arquivo enviado! ID: {response.get("id")}')
