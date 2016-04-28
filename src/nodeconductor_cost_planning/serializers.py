from __future__ import unicode_literals

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nodeconductor.core.serializers import JSONField, AugmentedSerializerMixin, GenericRelatedField
from nodeconductor.cost_tracking.serializers import PriceListItemSerializer
from nodeconductor.structure import SupportedServices

from . import models


class ConfigurationSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    variant = serializers.ReadOnlyField(source='get_variant_display')
    requirements = JSONField(source='metadata', read_only=True)

    class Meta:
        model = models.Configuration
        fields = ('url', 'uuid', 'name', 'category', 'variant', 'requirements')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid', 'view_name': 'deployment-configuration-detail'},
        }
        read_only_fields = 'name',


class DeploymentPlanItemSerializer(serializers.ModelSerializer):
    configuration = ConfigurationSerializer()
    price_list_item = PriceListItemSerializer()

    class Meta:
        model = models.DeploymentPlanItem
        fields = ('configuration', 'quantity', 'price_list_item')


class NestedDeploymentPlanItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeploymentPlanItem
        fields = ('configuration', 'quantity')
        extra_kwargs = {
            'configuration': {
                'lookup_field': 'uuid',
                'view_name': 'deployment-configuration-detail'
            }
        }

    def validate_configuration(self, configuration):
        if configuration.metadata == '':
            raise ValidationError('Configuration should have metadata')
        return configuration


class LazyServicesList(object):
    def __init__(self):
        self._items = None

    def __iter__(self):
        if self._items is None:
            self._items = [service['service'] for service in SupportedServices.get_service_models().values()]
        return iter(self._items)


class BaseDeploymentPlanSerializer(AugmentedSerializerMixin,
                                   serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeploymentPlan
        fields = 'url', 'uuid', 'name', 'customer', 'items', 'service'
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
                'view_name': 'deployment-plan-detail'
            },
            'customer': {'lookup_field': 'uuid'},
        }
        protected_fields = 'customer',

    service = GenericRelatedField(related_models=LazyServicesList(), required=False)


class DeploymentPlanSerializer(BaseDeploymentPlanSerializer):
    items = DeploymentPlanItemSerializer(many=True)


class DeploymentPlanCreateSerializer(BaseDeploymentPlanSerializer):
    items = NestedDeploymentPlanItemSerializer(many=True, required=False)

    def get_fields(self):
        fields = super(DeploymentPlanCreateSerializer, self).get_fields()
        fields['name'].required = False
        return fields

    def validate(self, attrs):
        if 'service' in attrs:
            customer = self.instance and self.instance.customer or attrs['customer']
            service = attrs['service']

            if service.customer != customer:
                raise ValidationError('Service should belong to the same customer')
        return attrs

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        plan = super(DeploymentPlanCreateSerializer, self).create(validated_data)
        for item in items:
            plan.items.create(**item)
        return plan

    def update(self, instance, validated_data):
        items = validated_data.pop('items', None)
        plan = super(DeploymentPlanCreateSerializer, self).update(instance, validated_data)
        if items is None:
            return plan

        current_map = {item.configuration_id: item.quantity for item in plan.items.all()}
        current_ids = set(current_map.keys())

        new_map = {item['configuration'].id: item['quantity'] for item in items}
        new_ids = set(new_map.keys())

        with transaction.atomic():
            # Remove stale items
            plan.items.filter(configuration_id__in=current_ids - new_ids).delete()

            # Create new items
            for item_id in new_ids - current_ids:
                plan.items.create(configuration_id=item_id, quantity=new_map[item_id])

            # Update existing items
            for item_id in new_ids & current_ids:
                plan.items.filter(configuration_id=item_id).update(quantity=new_map[item_id])

        return plan
