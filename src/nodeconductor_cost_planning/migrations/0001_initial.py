# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.utils.timezone
import uuidfield.fields
import model_utils.fields
import nodeconductor.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0034_change_service_settings_state_field'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('cost_tracking', '0019_priceestimate_limit'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150, verbose_name='name', validators=[nodeconductor.core.validators.validate_name])),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150, verbose_name='name', validators=[nodeconductor.core.validators.validate_name])),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32, editable=False, blank=True)),
                ('metadata', jsonfield.fields.JSONField(help_text='Metadata stores expected hardware configuration (RAM, CPU, HDD)', blank=True)),
                ('variant', models.CharField(max_length=150, choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')])),
                ('category', models.ForeignKey(to='nodeconductor_cost_planning.Category')),
            ],
            options={
                'ordering': ['category', 'name', 'variant'],
            },
        ),
        migrations.CreateModel(
            name='DeploymentPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=150, verbose_name='name', validators=[nodeconductor.core.validators.validate_name])),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32, editable=False, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('email_to', models.EmailField(max_length=254, blank=True)),
                ('content_type', models.ForeignKey(related_name='+', blank=True, to='contenttypes.ContentType', null=True)),
                ('customer', models.ForeignKey(related_name='+', to='structure.Customer')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='DeploymentPlanItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveSmallIntegerField()),
                ('configuration', models.ForeignKey(to='nodeconductor_cost_planning.Configuration')),
                ('plan', models.ForeignKey(related_name='items', to='nodeconductor_cost_planning.DeploymentPlan')),
                ('price_list_item', models.ForeignKey(related_name='+', blank=True, to='cost_tracking.PriceListItem', null=True)),
            ],
            options={
                'ordering': ('plan', 'configuration'),
            },
        ),
        migrations.AlterUniqueTogether(
            name='deploymentplanitem',
            unique_together=set([('plan', 'configuration')]),
        ),
    ]
