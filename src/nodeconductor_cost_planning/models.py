from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils import FieldTracker
from model_utils.models import TimeStampedModel

from nodeconductor.core import models as core_models
from nodeconductor.cost_tracking.models import PriceListItem, DefaultPriceListItem
from nodeconductor.structure import SupportedServices
from nodeconductor.structure.models import Customer


def get_service_content_types():
    services = [service['service'] for service in SupportedServices.get_service_models().values()]
    content_types = ContentType.objects.get_for_models(*services).values()
    return {'id__in': [ct.id for ct in content_types]}


@python_2_unicode_compatible
class DeploymentPlan(core_models.UuidMixin, core_models.NameMixin, TimeStampedModel):
    """
    Deployment plan contains list of plan items.
    """
    class Permissions(object):
        customer_path = 'customer'

    class Meta:
        ordering = ['-created']

    # Generic key to service
    content_type = models.ForeignKey(ContentType, null=True, blank=True, related_name='+',
                                     limit_choices_to=get_service_content_types)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    service = GenericForeignKey('content_type', 'object_id')

    customer = models.ForeignKey(Customer, related_name='+')
    email_to = models.EmailField(blank=True)
    tracker = FieldTracker()

    @property
    def service_has_changed(self):
        return self.tracker.has_changed('content_type_id')\
               or self.tracker.has_changed('object_id')

    @property
    def resource_content_type(self):
        if not self.service:
            return None
        resource = SupportedServices.get_related_models(self.service)['resources'][0]
        return ContentType.objects.get_for_model(resource)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class DeploymentPlanItem(models.Model):
    class Meta:
        ordering = 'plan', 'configuration'
        unique_together = 'plan', 'configuration'

    plan = models.ForeignKey(DeploymentPlan, related_name='items')
    configuration = models.ForeignKey('Configuration')
    quantity = models.PositiveSmallIntegerField()
    price_list_item = models.ForeignKey(PriceListItem, null=True, blank=True, related_name='+')
    tracker = FieldTracker()

    def update_price(self):
        # Skip invalid configuration
        if self.configuration.metadata == '':
            return

        price_item = self.find_price()

        # Skip extra database query
        if price_item != self.price_list_item:
            self.price_list_item = price_item
            self.save(update_fields=['price_list_item'])

    def find_price(self):
        """
        Find cheapest price list item which:
        1) matches configuration's requirements;
        2) belongs to plan's service provider.
        """
        price_item = None
        resource_content_type = self.plan.resource_content_type

        default_items = DefaultPriceListItem.objects.filter(resource_content_type=resource_content_type).exclude(metadata='')
        default_items = [item.key for item in default_items
                         if self.metadata_matches(self.configuration.metadata, item.metadata)]
        price_items = PriceListItem.objects.filter(
            key__in=default_items,
            resource_content_type=resource_content_type,
            content_type=self.plan.content_type,
            object_id=self.plan.object_id).\
            order_by('value')

        # Find cheapest offer
        if price_items.count() != 0:
            price_item = price_items[0]
        return price_item

    def metadata_matches(self, required, actual):
        for key, val in required.items():
            if key in actual and actual[key] >= required[key]:
                return True

    def __str__(self):
        return '%s %s' % (self.quantity, self.configuration)


@python_2_unicode_compatible
class Category(core_models.NameMixin):
    class Meta(object):
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Configuration(core_models.UuidMixin, core_models.NameMixin):
    class Meta:
        ordering = ['category', 'name', 'variant']

    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

    VARIANTS = (
        (SMALL, _('Small')),
        (MEDIUM, _('Medium')),
        (LARGE, _('Large')),
    )

    metadata = JSONField(blank=True, help_text="Metadata stores expected hardware configuration (RAM, CPU, HDD)")
    category = models.ForeignKey(Category)
    variant = models.CharField(max_length=150, choices=VARIANTS)

    def __str__(self):
        return '%s %s %s' % (self.get_variant_display(), self.name, self.category)
