# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-29 12:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import nodeconductor.core.fields
import nodeconductor.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('structure', '0052_customer_subnets'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, validators=[nodeconductor.core.validators.validate_name], verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='DeploymentPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=150, validators=[nodeconductor.core.validators.validate_name], verbose_name='name')),
                ('uuid', nodeconductor.core.fields.UUIDField()),
                ('certifications', models.ManyToManyField(blank=True, to='structure.ServiceCertification')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='structure.Project')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='DeploymentPlanItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='waldur_cost_planning.DeploymentPlan')),
            ],
            options={
                'ordering': ('plan', 'preset'),
            },
        ),
        migrations.CreateModel(
            name='Preset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, validators=[nodeconductor.core.validators.validate_name], verbose_name='name')),
                ('uuid', nodeconductor.core.fields.UUIDField()),
                ('variant', models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], max_length=150)),
                ('ram', models.PositiveIntegerField(default=0, help_text='Preset ram amount in MB.')),
                ('cores', models.PositiveIntegerField(default=0, help_text='Preset cores count.')),
                ('storage', models.PositiveIntegerField(default=0, help_text='Preset storage amount in MB.')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presets', to='waldur_cost_planning.Category')),
            ],
            options={
                'ordering': ('category', 'name', 'variant'),
            },
        ),
        migrations.AddField(
            model_name='deploymentplanitem',
            name='preset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='waldur_cost_planning.Preset'),
        ),
        migrations.AlterUniqueTogether(
            name='preset',
            unique_together=set([('category', 'name', 'variant')]),
        ),
        migrations.AlterUniqueTogether(
            name='deploymentplanitem',
            unique_together=set([('plan', 'preset')]),
        ),
    ]
