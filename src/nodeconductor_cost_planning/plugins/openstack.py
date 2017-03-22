""" Defines how to optimize OpenStack packages """
import collections

from rest_framework import serializers as rf_serializers

from nodeconductor_openstack.openstack import apps as openstack_apps

from .. import optimizers, register, serializers


OptimizedOpenStack = collections.namedtuple(
    'OptimizedOpenStack', field_names=optimizers.OptimizedService._fields + ('package_template',))


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

    def get_fields(self):
        fields = super(OptimizedOpenStackSerializer, self).get_fields()
        # XXX: Initialize 'package_template' field here to avoid circular dependency with assembly
        from nodeconductor_assembly_waldur.packages.serializers import PackageTemplateSerializer
        fields['package_template'] = PackageTemplateSerializer(read_only=True)
        return fields


register.Register.register_serializer(openstack_apps.OpenStackConfig.service_name, OptimizedOpenStackSerializer)
