""" Defines how to optimize OpenStack packages """
from rest_framework import serializers as rf_serializers

from nodeconductor_openstack.openstack import apps as openstack_apps

from .. import optimizers, register, serializers


class OptimizedOpenStack(optimizers.OptimizedService):
    """ Defines package template with the best price for OpenStack service """

    def __init__(self, service, price, package_template):
        super(OptimizedOpenStack, self).__init__(service, price)
        self.package_template = package_template


class OpenStackOptimizer(optimizers.Optimizer):
    """ Find the cheapest package template for OpenStack service """

    def optimize(self):
        # XXX: This import creates cyclic dependency with assembly module
        from nodeconductor_assembly_waldur.packages.models import PackageTemplate, PackageComponent
        requirements = self.deployment_plan.get_requirements()
        # Step 1. Find suitable templates.
        templates = PackageTemplate.objects.filter(
            service_settings=self.service.settings).prefetch_related('components')
        suitable_templates = []
        for template in templates:
            components = {c.type: c.amount for c in template.components.all()}
            is_suitable = (
                components[PackageComponent.Types.RAM] >= requirements['ram'] and
                components[PackageComponent.Types.STORAGE] >= requirements['storage'] and
                components[PackageComponent.Types.CORES] >= requirements['cores']
            )
            if is_suitable:
                suitable_templates.append(template)
        # Step 2. Find the cheapest template.
        if not suitable_templates:
            # return empty optimized service if there is no suitable templates
            return OptimizedOpenStack(self.service, price=None, package_template=None)
        cheapest_template = min(suitable_templates, key=lambda t: t.price)
        return OptimizedOpenStack(self.service, cheapest_template.price, cheapest_template)


register.Register.register_optimizer(openstack_apps.OpenStackConfig.service_name, OpenStackOptimizer)


class OptimizedOpenStackSerializer(serializers.OptimizedServiceSerializer):
    service = rf_serializers.HyperlinkedRelatedField(
        view_name='openstack-detail',
        lookup_field='uuid',
        read_only=True,
    )
    package_template = rf_serializers.HyperlinkedRelatedField(
        view_name='package-template-detail',
        lookup_field='uuid',
        read_only=True,
    )
    package_template_name = rf_serializers.ReadOnlyField(source='package_template.name')
    package_template_description = rf_serializers.ReadOnlyField(source='package_template.description')
    package_template_category = rf_serializers.ReadOnlyField(source='package_template.category')


register.Register.register_serializer(openstack_apps.OpenStackConfig.service_name, OptimizedOpenStackSerializer)
