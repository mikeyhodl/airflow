 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

``apache-airflow-providers-apache-beam``
========================================


.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Basics

    Home <self>
    Changelog <changelog>
    Security <security>

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: References

    Python API <_api/airflow/providers/apache/beam/index>

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: System tests

    System Tests <_api/tests/system/apache/beam/index>

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Resources

    PyPI Repository <https://pypi.org/project/apache-airflow-providers-apache-beam/>
    Example DAGs <https://github.com/apache/airflow/tree/providers-apache-beam/|version|/providers/apache/beam/tests/system/apache/beam>

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Guides

    Operators <operators>
    Installing from sources <installing-providers-from-sources>

.. THE REMAINDER OF THE FILE IS AUTOMATICALLY GENERATED. IT WILL BE OVERWRITTEN AT RELEASE TIME!


.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Commits

    Detailed list of commits <commits>


apache-airflow-providers-apache-beam package
------------------------------------------------------

`Apache Beam <https://beam.apache.org/>`__.


Release: 6.1.3

Release Date: ``|PypiReleaseDate|``

Provider package
----------------

This package is for the ``apache.beam`` provider.
All classes for this package are included in the ``airflow.providers.apache.beam`` python package.

Installation
------------

You can install this package on top of an existing Airflow 2 installation via
``pip install apache-airflow-providers-apache-beam``.
For the minimum Airflow version supported, see ``Requirements`` below.

Requirements
------------

The minimum Apache Airflow version supported by this provider distribution is ``2.10.0``.

==================  ==================================================================
PIP package         Version required
==================  ==================================================================
``apache-airflow``  ``>=2.10.0``
``apache-beam``     ``>=2.60.0; python_version < "3.13"``
``pyarrow``         ``>=16.1.0; python_version < "3.13"``
``numpy``           ``>=1.22.4; python_version < "3.11"``
``numpy``           ``>=1.23.2; python_version < "3.12" and python_version >= "3.11"``
``numpy``           ``>=1.26.0; python_version >= "3.12" and python_version < "3.13"``
==================  ==================================================================

Cross provider package dependencies
-----------------------------------

Those are dependencies that might be needed in order to use all the features of the package.
You need to install the specified provider distributions in order to use them.

You can install such cross-provider dependencies when installing from PyPI. For example:

.. code-block:: bash

    pip install apache-airflow-providers-apache-beam[common.compat]


==================================================================================================================  =================
Dependent package                                                                                                   Extra
==================================================================================================================  =================
`apache-airflow-providers-common-compat <https://airflow.apache.org/docs/apache-airflow-providers-common-compat>`_  ``common.compat``
`apache-airflow-providers-google <https://airflow.apache.org/docs/apache-airflow-providers-google>`_                ``google``
==================================================================================================================  =================

Downloading official packages
-----------------------------

You can download officially released packages and verify their checksums and signatures from the
`Official Apache Download site <https://downloads.apache.org/airflow/providers/>`_

* `The apache-airflow-providers-apache-beam 6.1.3 sdist package <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3.tar.gz>`_ (`asc <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3.tar.gz.asc>`__, `sha512 <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3.tar.gz.sha512>`__)
* `The apache-airflow-providers-apache-beam 6.1.3 wheel package <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3-py3-none-any.whl>`_ (`asc <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3-py3-none-any.whl.asc>`__, `sha512 <https://downloads.apache.org/airflow/providers/apache_airflow_providers_apache_beam-6.1.3-py3-none-any.whl.sha512>`__)
