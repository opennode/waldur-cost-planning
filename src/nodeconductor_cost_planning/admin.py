from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ungettext

from nodeconductor.core.tasks import send_task
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
    actions = ['generate_pdf']

    def generate_pdf(self, request, queryset):
        for plan in queryset.iterator():
            send_task('cost_planning', 'generate_pdf')(plan.id)

        tasks_scheduled = queryset.count()
        message = ungettext(
            'Scheduled generation of PDF for one deployment plan.',
            'Scheduled generation of PDF for %(tasks_scheduled)d deployment plans.',
            tasks_scheduled
        )
        message = message % {
            'tasks_scheduled': tasks_scheduled,
        }

        self.message_user(request, message)

    generate_pdf.short_description = "Generate PDF"


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Configuration, ConfigurationAdmin)
admin.site.register(models.DeploymentPlan, DeploymentPlanAdmin)
