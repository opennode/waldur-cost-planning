""" Defines how to optimize price for OpenStackTenant instances """
import collections

from rest_framework import serializers as rf_serializers

from nodeconductor_openstack.openstack_tenant import apps as ot_apps, models as ot_models, serializers as ot_serializers

from .. import optimizers, register, serializers


OptimizedPreset = collections.namedtuple(
    'OptimizedPreset', ('preset', 'flavor', 'quantity', 'price', 'flavor_price', 'storage_price'))


OptimizedOpenStackTenant = optimizers.namedtuple_with_defaults(
    'OptimizedOpenStack',
    field_names=optimizers.OptimizedService._fields + ('optimized_presets',),
    default_values=optimizers.OptimizedService._defaults,
)


class OpenStackTenantOptimizer(optimizers.Optimizer):
    """ Find the cheapest OpenStackTenant flavor for each preset. """

    def _get_cheapest_flavor(self, suitable_flavors):
        # TODO
        return suitable_flavors[0], 0

    def _get_storage_price(self, storage):
        # TODO
        return 1

    def optimize(self, deployment_plan, service):
        optimized_presets = []
        price = 0
        for item in deployment_plan.items.all():
            preset = item.preset
            suitable_flavors = ot_models.Flavor.objects.filter(
                cores__gte=preset.cores, ram__gte=preset.ram, settings=service.settings)
            if not suitable_flavors:
                preset_as_str = '%s (cores: %s, ram %s MB, storage %s MB)' % (
                    preset.name, preset.cores, preset.ram, preset.storage)
                raise optimizers.OptimizationError(
                    'It is impossible to create an instance for preset %s. It is too big.' % preset_as_str)

            flavor, flavor_price = self._get_cheapest_flavor(suitable_flavors)
            storage_price = self._get_storage_price(preset.storage)
            preset_price = flavor_price + storage_price
            optimized_presets.append(OptimizedPreset(
                preset=preset,
                flavor=flavor,
                quantity=item.quantity,
                flavor_price=flavor_price,
                storage_price=storage_price,
                price=preset_price * item.quantity,
            ))
            price += preset_price * item.quantity
        return OptimizedOpenStackTenant(price=price, service=service, optimized_presets=optimized_presets)


register.Register.register_optimizer(ot_apps.OpenStackTenantConfig.service_name, OpenStackTenantOptimizer)


class OptimizedPresetSerializer(rf_serializers.Serializer):
    flavor = ot_serializers.FlavorSerializer()
    preset = serializers.PresetSerializer()
    quantity = rf_serializers.IntegerField()
    flavor_price = rf_serializers.DecimalField(max_digits=22, decimal_places=10)
    storage_price = rf_serializers.DecimalField(max_digits=22, decimal_places=10)
    price = rf_serializers.DecimalField(max_digits=22, decimal_places=10)


class OptimizedOpenStackTenantSerializer(serializers.OptimizedServiceSerializer):
    service = rf_serializers.HyperlinkedRelatedField(
        view_name='openstacktenant-detail',
        lookup_field='uuid',
        read_only=True,
    )
    optimized_presets = OptimizedPresetSerializer(many=True)


register.Register.register_serializer(ot_apps.OpenStackTenantConfig.service_name, OptimizedOpenStackTenantSerializer)
