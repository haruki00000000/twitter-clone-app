# Generated by Django 2.2.17 on 2021-02-19 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='like',
            field=models.PositiveIntegerField(default=0),
        ),
    ]