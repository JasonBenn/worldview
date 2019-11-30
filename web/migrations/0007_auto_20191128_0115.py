# Generated by Django 2.2.7 on 2019-11-28 01:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_notiondocument_parent_notion_document'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='source_author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='web.GoodreadsAuthor'),
        ),
        migrations.AlterField(
            model_name='text',
            name='source_book',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='web.GoodreadsBook'),
        ),
        migrations.AlterField(
            model_name='text',
            name='source_notion_document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='web.NotionDocument'),
        ),
        migrations.AlterField(
            model_name='text',
            name='source_series',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='web.GoodreadsSeries'),
        ),
    ]