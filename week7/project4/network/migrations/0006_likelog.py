# Generated by Django 5.2.3 on 2025-07-05 09:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0005_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='LikeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('like', 'Like'), ('unlike', 'Unlike')], max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='like_logs', to='network.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='like_logs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
