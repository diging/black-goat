# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-10 17:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goat', '0005_authority_namespace'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concept',
            name='authority',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='concepts', to='goat.Authority'),
        ),
    ]
