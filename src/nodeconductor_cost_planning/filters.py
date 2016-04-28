import django_filters

from . import models


class DeploymentPlanFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(
        name='customer__uuid',
        distinct=True,
    )

    class Meta(object):
        model = models.DeploymentPlan
        fields = ['customer']

        order_by = [
            'name',
            '-name',
            'created',
            '-created'
        ]
