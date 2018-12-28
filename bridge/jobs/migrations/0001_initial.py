# Generated by Django 2.1.3 on 2018-12-28 12:02

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024)),
            ],
            options={
                'db_table': 'file_system',
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('name', models.CharField(db_index=True, max_length=150, unique=True)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('format', models.PositiveSmallIntegerField(default=1, editable=False)),
                ('status', models.CharField(choices=[('0', 'Not solved'), ('1', 'Pending'), ('2', 'Is solving'), ('3', 'Solved'), ('4', 'Failed'), ('5', 'Corrupted'), ('6', 'Cancelling'), ('7', 'Cancelled'), ('8', 'Terminated')], default='0', max_length=1)),
                ('weight', models.CharField(choices=[('0', 'Full-weight'), ('1', 'Lightweight')], default='0', max_length=1)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                'db_table': 'job',
            },
        ),
        migrations.CreateModel(
            name='JobFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_sum', models.CharField(db_index=True, max_length=255)),
                ('file', models.FileField(upload_to='Job')),
            ],
            options={
                'db_table': 'job_file',
            },
        ),
        migrations.CreateModel(
            name='JobHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('change_date', models.DateTimeField()),
                ('comment', models.CharField(blank=True, default='', max_length=255)),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField(default='')),
                ('global_role', models.CharField(choices=[('0', 'No access'), ('1', 'Observer'), ('2', 'Expert'), ('3', 'Observer and Operator'), ('4', 'Expert and Operator')], default='0', max_length=1)),
            ],
            options={
                'db_table': 'jobhistory',
                'ordering': ('-version',),
            },
        ),
        migrations.CreateModel(
            name='RunHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(db_index=True)),
                ('status', models.CharField(choices=[('0', 'Not solved'), ('1', 'Pending'), ('2', 'Is solving'), ('3', 'Solved'), ('4', 'Failed'), ('5', 'Corrupted'), ('6', 'Cancelling'), ('7', 'Cancelled'), ('8', 'Terminated')], default='1', max_length=1)),
            ],
            options={
                'db_table': 'job_run_history',
            },
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('0', 'No access'), ('1', 'Observer'), ('2', 'Expert'), ('3', 'Observer and Operator'), ('4', 'Expert and Operator')], max_length=1)),
                ('job_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.JobHistory')),
            ],
            options={
                'db_table': 'user_job_role',
            },
        ),
    ]
