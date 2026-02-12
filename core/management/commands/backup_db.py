"""
Management command to backup the database and upload to Google Cloud Storage.
Usage:
    python manage.py backup_db               # Backup to GCS
    python manage.py backup_db --local-only   # Backup locally only
"""
import os
import gzip
import subprocess
from datetime import datetime
from io import BytesIO

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup PostgreSQL database and upload to Google Cloud Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-only',
            action='store_true',
            help='Only save locally, do not upload to GCS',
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f'g7serv_{timestamp}.sql'
        filename_gz = f'{filename}.gz'
        
        # Get database URL from settings
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']
        db_password = db_settings.get('PASSWORD', '')
        
        self.stdout.write(f'Starting backup of database: {db_name}')
        
        # Build pg_dump command
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password
        
        cmd = [
            'pg_dump',
            '-h', str(db_host),
            '-p', str(db_port),
            '-U', str(db_user),
            '-d', str(db_name),
            '--no-owner',
            '--no-privileges',
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, env=env, timeout=300
            )
            if result.returncode != 0:
                raise CommandError(f'pg_dump failed: {result.stderr}')
        except FileNotFoundError:
            raise CommandError(
                'pg_dump not found. Install PostgreSQL client tools.'
            )
        
        sql_data = result.stdout.encode('utf-8')
        self.stdout.write(f'Database dump size: {len(sql_data) / 1024 / 1024:.1f} MB')
        
        # Compress with gzip
        compressed = BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
            gz.write(sql_data)
        compressed_data = compressed.getvalue()
        self.stdout.write(f'Compressed size: {len(compressed_data) / 1024 / 1024:.1f} MB')
        
        # Save locally
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        local_path = backup_dir / filename_gz
        with open(local_path, 'wb') as f:
            f.write(compressed_data)
        self.stdout.write(self.style.SUCCESS(f'Local backup saved: {local_path}'))
        
        if options['local_only']:
            return
        
        # Upload to GCS
        bucket_name = getattr(settings, 'GS_BUCKET_NAME', None)
        if not bucket_name:
            self.stdout.write(self.style.WARNING(
                'GCS_BUCKET_NAME not set. Skipping cloud upload.'
            ))
            return
        
        try:
            from google.cloud import storage as gcs_storage
            
            gcs_creds = getattr(settings, 'GS_CREDENTIALS', None)
            if gcs_creds:
                client = gcs_storage.Client(credentials=gcs_creds)
            else:
                client = gcs_storage.Client()
            
            bucket = client.bucket(bucket_name)
            blob_name = f'backups/db/{filename_gz}'
            blob = bucket.blob(blob_name)
            blob.upload_from_string(compressed_data, content_type='application/gzip')
            
            self.stdout.write(self.style.SUCCESS(
                f'Uploaded to GCS: gs://{bucket_name}/{blob_name}'
            ))
            
            # Clean up old backups (keep last 30)
            blobs = list(bucket.list_blobs(prefix='backups/db/'))
            if len(blobs) > 30:
                blobs.sort(key=lambda b: b.time_created)
                for old_blob in blobs[:-30]:
                    old_blob.delete()
                    self.stdout.write(f'Deleted old backup: {old_blob.name}')
            
        except Exception as e:
            raise CommandError(f'GCS upload failed: {e}')
        
        self.stdout.write(self.style.SUCCESS('Backup completed successfully!'))
