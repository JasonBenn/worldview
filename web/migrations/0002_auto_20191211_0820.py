# Generated by Django 2.2.7 on 2019-12-11 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notiondocument',
            name='url',
            field=models.TextField(unique=True),
        ),
    ]
