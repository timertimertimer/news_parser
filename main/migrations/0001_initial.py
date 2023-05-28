# Generated by Django 4.2 on 2023-05-06 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.CharField(max_length=255, unique=True)),
                ('source', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('date', models.IntegerField(blank=True, null=True)),
                ('category', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('text', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
