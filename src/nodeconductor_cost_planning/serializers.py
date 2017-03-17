from __future__ import unicode_literals

from django.db import transaction
from rest_framework import serializers

from nodeconductor.core import serializers as core_serializers
from nodeconductor.structure import permissions as structure_permissions

from . import models


class PresetSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = models.Preset
        fields = ('url', 'uuid', 'name', 'category', 'ram', 'cores', 'storage')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid', 'view_name': 'deployment-preset-detail'},
        }


class DeploymentPlanItemSerializer(serializers.ModelSerializer):
    preset = PresetSerializer()

    class Meta:
        model = models.DeploymentPlanItem
        fields = ('preset', 'quantity',)


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


class BaseDeploymentPlanSerializer(core_serializers.AugmentedSerializerMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.DeploymentPlan
        fields = ('url', 'uuid', 'name', 'customer', 'items')
        protected_fields = ('customer',)
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'customer': {'lookup_field': 'uuid'},
        }


class DeploymentPlanSerializer(BaseDeploymentPlanSerializer):
    items = DeploymentPlanItemSerializer(many=True)


class DeploymentPlanCreateSerializer(BaseDeploymentPlanSerializer):
    items = NestedDeploymentPlanItemSerializer(many=True, required=False)

    def validate_customer(self, customer):
        structure_permissions.is_owner(self.context['request'], self.context['view'], customer)
        return customer

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
