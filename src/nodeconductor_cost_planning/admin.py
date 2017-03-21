from __future__ import unicode_literals

from django.contrib import admin

from . import models


class PresetAdmin(admin.ModelAdmin):
    list_display = ('category', 'variant', 'name', 'ram', 'cores', 'storage')
    list_filter = ('category',)


class PresetInline(admin.TabularInline):
    model = models.Preset
    extra = 1


class CategoryAdmin(admin.ModelAdmin):
    inlines = (PresetInline,)


class DeploymentPlanItem(admin.TabularInline):
    model = models.DeploymentPlanItem
    extra = 1
    fields = ('preset', 'quantity')


class DeploymentPlanAdmin(admin.ModelAdmin):
    inlines = (DeploymentPlanItem,)
    search_fields = ('name',)
    list_display = ('name', 'project')


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Preset, PresetAdmin)
admin.site.register(models.DeploymentPlan, DeploymentPlanAdmin)
