""" Defines how to optimize DigitalOcean droplets sizes """
import collections

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers as rf_serializers

from nodeconductor.cost_tracking import models as cost_tracking_models
from nodeconductor_digitalocean import apps as do_apps, models as do_models, serializers as do_serializers

from .. import optimizers, register, serializers


OptimizedPreset = collections.namedtuple('OptimizedPreset', ('preset', 'size', 'quantity', 'price'))

OptimizedDigitalOcean = optimizers.namedtuple_with_defaults(
    'OptimizedDigitalOcean',
    field_names=optimizers.OptimizedService._fields + ('optimized_presets',),
    default_values=optimizers.OptimizedService._defaults,
)


class DigitalOceanOptimizer(optimizers.Optimizer):
    """ Find the cheapest Digital Ocean size for each preset """
    HOURS_IN_DAY = 24
    DAYS_IN_MONTH = 30

    def _get_service_price_list_items(self, service, resource_model):
        """ Return all price list item that belongs to given service """
        resource_content_type = ContentType.objects.get_for_model(resource_model)
        default_items = set(cost_tracking_models.DefaultPriceListItem.objects.filter(
            resource_content_type=resource_content_type))
        items = set(cost_tracking_models.PriceListItem.objects.filter(
            default_price_list_item__in=default_items, service=service).select_related('default_price_list_item'))
        rewrited_defaults = set([i.default_price_list_item for i in items])
        return items | (default_items - rewrited_defaults)

    def _get_size_prices(self, service):
        """ Return dicti with items <size>: <size price> """
        sizes = do_models.Size.objects.all()
        size_prices = {item.key: item.value for item in
                       self._get_service_price_list_items(service, do_models.Droplet)}
        return {size: size_prices.get(size.name, size.price) * self.HOURS_IN_DAY for size in sizes}

    def optimize(self, deployment_plan, service):
        optimized_presets = []
        price = 0
        size_prices = self._get_size_prices(service)
        for item in deployment_plan.items.all():
            preset = item.preset
            sizes = do_models.Size.objects.filter(
                cores__gte=preset.cores, ram__gte=preset.ram, disk__gte=preset.storage)
            if not sizes:
                preset_as_str = '%s (cores: %s, ram %s MB, storage %s MB)' % (
                    preset.name, preset.cores, preset.ram, preset.storage)
                raise optimizers.OptimizationError(
                    'It is impossible to create a droplet for preset %s. It is too big.' % preset_as_str)
            try:
                size = min(sizes, key=lambda size: size_prices[size])
            except ValueError:
                raise optimizers.OptimizationError('Price for size %s is not defined' % size.name)
            optimized_presets.append(OptimizedPreset(
                preset=preset,
                size=size,
                quantity=item.quantity,
                price=size_prices[size] * item.quantity,
            ))
            price += size_prices[size] * item.quantity
        return OptimizedDigitalOcean(price=price, service=service, optimized_presets=optimized_presets)


register.Register.register_optimizer(do_apps.DigitalOceanConfig.service_name, DigitalOceanOptimizer)


class OptimizedPresetSerializer(rf_serializers.Serializer):
    size = do_serializers.SizeSerializer()
    preset = serializers.PresetSerializer()
    quantity = rf_serializers.IntegerField()
    price = rf_serializers.DecimalField(max_digits=22, decimal_places=10)


class OptimizedDigitalOceanSerializer(serializers.OptimizedServiceSerializer):
    service = rf_serializers.HyperlinkedRelatedField(
        view_name='digitalocean-detail',
        lookup_field='uuid',
        read_only=True,
    )
    optimized_presets = OptimizedPresetSerializer(many=True)


register.Register.register_serializer(do_apps.DigitalOceanConfig.service_name, OptimizedDigitalOceanSerializer)
