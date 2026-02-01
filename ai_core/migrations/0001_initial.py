from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AtendimentoAI',
            fields=[
                ('id', models.BigAutoField(auto_now_add=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('cliente_nome', models.CharField(default='Anônimo', max_length=100)),
                ('mensagem_usuario', models.TextField()),
                ('categoria_detectada', models.CharField(choices=[('orcamento', 'Orçamento/Comercial'), ('suporte', 'Suporte Técnico/OS'), ('financeiro', 'Financeiro/Boletos'), ('outro', 'Outros Assuntos')], max_length=20)),
                ('protocolo', models.CharField(max_length=20, unique=True)),
                ('resolvido', models.BooleanField(default=False)),
            ],
        ),
    ]
