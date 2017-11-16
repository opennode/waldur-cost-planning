from django.apps import AppConfig


class CostPlanningConfig(AppConfig):
    name = 'nodeconductor_cost_planning'
    verbose_name = 'Cost planning'

    def ready(self):
        from .plugins import digitalocean, openstack_tenant, aws, azure
