# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-05 14:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('marks', '0008_auto'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnsafeAssociationLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dislike', models.BooleanField(default=False)),
                ('association', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.MarkUnsafeReport')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mark_association_like',
            },
        ),
    ]