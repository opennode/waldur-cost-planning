from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ungettext

from nodeconductor.core.tasks import send_task
from . import models


class PresetItemInline(admin.TabularInline):
    model = models.PresetItem
    extra = 1


class PresetAdmin(admin.ModelAdmin):
    list_display = 'category', 'variant', 'name'
    list_filter = 'category',
    inlines = PresetItemInline,


class PresetInline(admin.TabularInline):
    model = models.Preset
    extra = 1


class CategoryAdmin(admin.ModelAdmin):
    inlines = PresetInline,


class DeploymentPlanItem(admin.TabularInline):
    model = models.DeploymentPlanItem
    extra = 1
    fields = 'preset', 'quantity', 'total_price'
    readonly_fields = 'total_price',


class DeploymentPlanAdmin(admin.ModelAdmin):
    inlines = DeploymentPlanItem,
    search_fields = 'name',
    list_display = 'name', 'customer'
    actions = ['generate_pdf', 'send_report']

    def generate_pdf(self, request, queryset):
        for plan in queryset.iterator():
            send_task('cost_planning', 'generate_pdf')(plan.uuid.hex)

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

    def send_report(self, request, queryset):
        plans = queryset.exclude(email_to='')
        for plan in plans:
            send_task('cost_planning', 'send_report')(plan.uuid.hex)

        tasks_scheduled = plans.count()
        message = ungettext(
            'Sending emails for one plan.',
            'Sending emails for %(tasks_scheduled)d plans.',
            tasks_scheduled
        )
        message = message % {
            'tasks_scheduled': tasks_scheduled,
        }

        self.message_user(request, message)

    send_report.short_description = "Send email with plan details"


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Preset, PresetAdmin)
admin.site.register(models.DeploymentPlan, DeploymentPlanAdmin)
