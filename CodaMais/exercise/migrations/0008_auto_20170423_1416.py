# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-23 14:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercise', '0007_auto_20170409_0308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='input_exercise',
            field=models.CharField(max_length=15),
        ),
    ]