from django.apps import AppConfig


class CostPlanningConfig(AppConfig):
    name = 'nodeconductor_cost_planning'
    verbose_name = 'Cost planning'

    def ready(self):
        # import here to register openstack plugin.
        from .plugins import openstack, digitalocean, openstack_tenant, aws, azure
