Welcome to Waldur cost planning plugin's documentation!
==============================================================

This plugin allows to get a price estimate without actually creating the infrastructure.
Consider example workflow:

- admin creates categories: webservers and databases;
- admin creates presets, Apache and MySQL, each preset is linked to set of default price list items;
- user creates new deployment plan for his customer;
- user selects several presets, for example 20 MySQL databases and 2 Apache servers;
- user selects service, for example Azure;
- price list items are found by matching default price list items of presets against selected service;
- total price for deployment plan is calculated;
- user generates and downloads PDF report with deployment plan details;
- user sends email with deployment plan details to another user.

Guide
-----

.. toctree::
   :maxdepth: 1

   installation

API
---

.. toctree::
   :maxdepth: 1

   api

Endpoints
---------

.. toctree::
   :maxdepth: 1

   drfapi/index

License
-------

NodeConductor cost planning plugin is open-source under MIT license.


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

