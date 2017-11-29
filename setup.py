#!/usr/bin/env python
from setuptools import setup, find_packages


dev_requires = [
    'Sphinx==1.2.2',
]

install_requires = [
    'nodeconductor>=0.142.0',
    'waldur_openstack>=0.30.2',
    'waldur_digitalocean>=0.8.2',
    'waldur_aws>=0.9.2',
    'waldur_azure>=0.3.0',
]

setup(
    name='waldur-cost-planning',
    version='0.5.5',
    author='OpenNode Team',
    author_email='info@opennodecloud.com',
    url='http://waldur.com',
    description='Waldur cost planning plugin allows to get a price estimate without actually creating the infrastructure.',
    long_description=open('README.rst').read(),
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=install_requires,
    zip_safe=False,
    extras_require={
        'dev': dev_requires,
    },
    entry_points={
        'nodeconductor_extensions': (
            'waldur_cost_planning = waldur_cost_planning.extension:CostPlanningExtension',
        ),
    },
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
)
