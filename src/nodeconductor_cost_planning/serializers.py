from __future__ import unicode_literals

from django.db import transaction
from rest_framework import serializers

from nodeconductor.core import serializers as core_serializers
from nodeconductor.structure import permissions as structure_permissions, models as structure_models
from . import models


class PresetSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    variant = serializers.ReadOnlyField(source='get_variant_display')

    class Meta:
        model = models.Preset
        fields = ('url', 'uuid', 'name', 'category', 'variant', 'ram', 'cores', 'storage')
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


class NestedCertificatesSerializer(core_serializers.HyperlinkedRelatedModelSerializer):
    class Meta:
        model = structure_models.ServiceCertification
        fields = ('url', 'uuid', 'name', 'description', 'link')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid', 'view_name': 'service-certification-detail'},
        }


class BaseDeploymentPlanSerializer(core_serializers.AugmentedSerializerMixin, serializers.HyperlinkedModelSerializer):
    certifications = NestedCertificatesSerializer(
        many=True, queryset=structure_models.ServiceCertification.objects.all(), required=False)

    class Meta:
        model = models.DeploymentPlan
        fields = ('url', 'uuid', 'name', 'customer', 'items', 'certifications')
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
        certifications = validated_data.pop('certifications', [])
        plan = super(DeploymentPlanCreateSerializer, self).create(validated_data)
        for item in items:
            plan.items.create(**item)
        plan.certifications.add(*certifications)
        return plan

    def update(self, instance, validated_data):
        items = validated_data.pop('items', None)
        certifications = validated_data.pop('certifications', None)

        plan = super(DeploymentPlanCreateSerializer, self).update(instance, validated_data)

        if certifications is not None:
            with transaction.atomic():
                plan.certifications.clear()
                plan.certifications.add(*certifications)

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


class OptimizedServiceSummarySerializer(serializers.Serializer):
    """ Serializer that renders each instance with its own specific serializer """

    @classmethod
    def get_serializer(cls, service_type):
        from nodeconductor_openstack.openstack.apps import OpenStackConfig
        serializers = {
            OpenStackConfig.service_name: OptimizedOpenStackSerializer,
        }
        return serializers.get(service_type, OptimizedServiceSerializer)

    def to_representation(self, instance):
        serializer = self.get_serializer(instance.service.settings.type)
        return serializer(instance, context=self.context).data


class OptimizedServiceSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=22, decimal_places=10)
    service_settings = serializers.HyperlinkedRelatedField(
        source='service.settings',
        view_name='servicesettings-detail',
        lookup_field='uuid',
        read_only=True,
    )
    service_settings_name = serializers.ReadOnlyField(source='service.settings.name')
    service_settings_type = serializers.ReadOnlyField(source='service.settings.type')


class OptimizedOpenStackSerializer(OptimizedServiceSerializer):
    service = serializers.HyperlinkedRelatedField(
        view_name='openstack-detail',
        lookup_field='uuid',
        read_only=True,
    )
    package_template = serializers.HyperlinkedRelatedField(
        view_name='package-template-detail',
        lookup_field='uuid',
        read_only=True,
    )
    package_template_name = serializers.ReadOnlyField(source='package_template.name')
    package_template_description = serializers.ReadOnlyField(source='package_template.description')
    package_template_category = serializers.ReadOnlyField(source='package_template.category')
