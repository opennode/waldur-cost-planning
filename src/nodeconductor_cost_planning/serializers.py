from __future__ import unicode_literals

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nodeconductor.core.serializers import JSONField, AugmentedSerializerMixin, GenericRelatedField
from nodeconductor.structure import SupportedServices

from . import models


class PresetSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    variant = serializers.ReadOnlyField(source='get_variant_display')

    class Meta:
        model = models.Preset
        fields = ('url', 'uuid', 'name', 'category', 'variant')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid', 'view_name': 'deployment-preset-detail'},
        }


class DeploymentPlanItemSerializer(serializers.ModelSerializer):
    preset = PresetSerializer()

    class Meta:
        model = models.DeploymentPlanItem
        fields = ('preset', 'quantity', 'total_price')


class NestedDeploymentPlanItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeploymentPlanItem
        fields = ('preset', 'quantity')
        extra_kwargs = {
            'preset': {
                'lookup_field': 'uuid',
                'view_name': 'deployment-preset-detail'
            }
        }


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
        fields = 'url', 'uuid', 'name', 'customer', 'items', 'service', 'total_price'
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

        current_map = {item.preset_id: item.quantity for item in plan.items.all()}
        current_ids = set(current_map.keys())

        new_map = {item['preset'].id: item['quantity'] for item in items}
        new_ids = set(new_map.keys())

        with transaction.atomic():
            # Remove stale items
            plan.items.filter(preset_id__in=current_ids - new_ids).delete()

            # Create new items
            for item_id in new_ids - current_ids:
                plan.items.create(preset_id=item_id, quantity=new_map[item_id])

            # Update existing items
            for item_id in new_ids & current_ids:
                plan.items.filter(preset_id=item_id).update(quantity=new_map[item_id])

        return plan
