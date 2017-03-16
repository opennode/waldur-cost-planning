import django_filters

from . import models


class DeploymentPlanFilter(django_filters.FilterSet):
    customer = django_filters.UUIDFilter(
        name='customer__uuid',
        distinct=True,
    )
    o = django_filters.OrderingFilter(
        fields=('name', 'created')
    )

    class Meta(object):
        model = models.DeploymentPlan
