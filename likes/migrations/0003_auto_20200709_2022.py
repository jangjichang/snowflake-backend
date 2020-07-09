# Generated by Django 3.0.7 on 2020-07-09 11:22

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('likes', '0002_auto_20200530_1720'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='like',
            unique_together={('content_type', 'object_id', 'user')},
        ),
    ]