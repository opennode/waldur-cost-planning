from __future__ import unicode_literals

from django.contrib import admin

from . import models


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = 'category', 'variant', 'name'
    list_filter = 'category',


class ConfigurationInline(admin.TabularInline):
    model = models.Configuration
    extra = 1


class CategoryAdmin(admin.ModelAdmin):
    inlines = ConfigurationInline,


class DeploymentPlanItem(admin.TabularInline):
    model = models.DeploymentPlanItem
    extra = 1


class DeploymentPlanAdmin(admin.ModelAdmin):
    inlines = DeploymentPlanItem,
    search_fields = 'name',
    list_display = 'name', 'customer', 'resource_content_type'


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Configuration, ConfigurationAdmin)
admin.site.register(models.DeploymentPlan, DeploymentPlanAdmin)
