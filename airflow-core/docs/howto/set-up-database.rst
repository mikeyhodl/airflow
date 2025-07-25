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

.. _set-up-database-backend:

Set up a Database Backend
=========================

Airflow was built to interact with its metadata using `SqlAlchemy <https://docs.sqlalchemy.org/en/14/>`__.

The document below describes the database engine configurations, the necessary changes to their configuration to be used with Airflow, as well as changes to the Airflow configurations to connect to these databases.

Choosing database backend
-------------------------

If you want to take a real test drive of Airflow, you should consider setting up a database backend to **PostgreSQL** or **MySQL**.
By default, Airflow uses **SQLite**, which is intended for development purposes only.

Airflow supports the following database engine versions, so make sure which version you have. Old versions may not support all SQL statements.

* PostgreSQL: 12, 13, 14, 15, 16
* MySQL: 8.0, `Innovation <https://dev.mysql.com/blog-archive/introducing-mysql-innovation-and-long-term-support-lts-versions>`_
* SQLite: 3.15.0+

If you plan on running more than one scheduler, you have to meet additional requirements.
For details, see :ref:`Scheduler HA Database Requirements <scheduler:ha:db_requirements>`.

.. warning::

  Despite big similarities between MariaDB and MySQL, we DO NOT support MariaDB as a backend for Airflow.
  There are known problems (for example index handling) between MariaDB and MySQL and we do not test
  our migration scripts nor application execution on Maria DB. We know there were people who used
  MariaDB for Airflow and that cause a lot of operational headache for them so we strongly discourage
  attempts of using MariaDB as a backend and users cannot expect any community support for it
  because the number of users who tried to use MariaDB for Airflow is very small.

Database URI
------------

Airflow uses SQLAlchemy to connect to the database, which requires you to configure the Database URL.
You can do this in option ``sql_alchemy_conn`` in section ``[database]``. It is also common to configure
this option with ``AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`` environment variable.

.. note::
    For more information on setting the configuration, see :doc:`/howto/set-config`.

If you want to check the current value, you can use ``airflow config get-value database sql_alchemy_conn`` command as in
the example below.

.. code-block:: bash

    $ airflow config get-value database sql_alchemy_conn
    sqlite:////tmp/airflow/airflow.db

The exact format description is described in the SQLAlchemy documentation, see `Database Urls <https://docs.sqlalchemy.org/en/14/core/engines.html>`__. We will also show you some examples below.

Setting up a SQLite Database
----------------------------

SQLite database can be used to run Airflow for development purpose as it does not require any database server
(the database is stored in a local file). There are plenty of limitations of using the SQLite database which you can
easily find online, and it should NEVER be used for production.

There is a minimum version of sqlite3 required to run Airflow 2.0+ - minimum version is 3.15.0. Some of the
older systems have an earlier version of sqlite installed by default and for those system you need to manually
upgrade SQLite to use version newer than 3.15.0. Note, that this is not a ``python library`` version, it's the
SQLite system-level application that needs to be upgraded. There are different ways how SQLite might be
installed, you can find some information about that at the `official website of SQLite
<https://www.sqlite.org/index.html>`_ and in the documentation specific to distribution of your Operating
System.

**Troubleshooting**

Sometimes even if you upgrade SQLite to higher version and your local python reports higher version,
the python interpreter used by Airflow might still use the older version available in the
``LD_LIBRARY_PATH`` set for the python interpreter that is used to start Airflow.

You can make sure which version is used by the interpreter by running this check:

.. code-block:: bash

    root@b8a8e73caa2c:/opt/airflow# python
    Python 3.8.10 (default, Mar 15 2022, 12:22:08)
    [GCC 8.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sqlite3
    >>> sqlite3.sqlite_version
    '3.27.2'
    >>>

But be aware that setting environment variables for your Airflow deployment might change which SQLite
library is found first, so you might want to make sure that the "high-enough" version of SQLite is the only
version installed in your system.

An example URI for the sqlite database:

.. code-block:: text

    sqlite:////home/airflow/airflow.db

**Upgrading SQLite on AmazonLinux AMI or Container Image**

AmazonLinux SQLite can only be upgraded to v3.7 using the source repos. Airflow requires v3.15 or higher. Use the
following instructions to setup the base image (or AMI) with latest SQLite3

Pre-requisite: You will need ``wget``, ``tar``, ``gzip``, ``gcc``, ``make``, and ``expect`` to get the upgrade process working.

.. code-block:: bash

  yum -y install wget tar gzip gcc make expect

Download source from https://sqlite.org/, make and install locally.

.. code-block:: bash

    wget https://www.sqlite.org/src/tarball/sqlite.tar.gz
    tar xzf sqlite.tar.gz
    cd sqlite/
    export CFLAGS="-DSQLITE_ENABLE_FTS3 \
        -DSQLITE_ENABLE_FTS3_PARENTHESIS \
        -DSQLITE_ENABLE_FTS4 \
        -DSQLITE_ENABLE_FTS5 \
        -DSQLITE_ENABLE_JSON1 \
        -DSQLITE_ENABLE_LOAD_EXTENSION \
        -DSQLITE_ENABLE_RTREE \
        -DSQLITE_ENABLE_STAT4 \
        -DSQLITE_ENABLE_UPDATE_DELETE_LIMIT \
        -DSQLITE_SOUNDEX \
        -DSQLITE_TEMP_STORE=3 \
        -DSQLITE_USE_URI \
        -O2 \
        -fPIC"
    export PREFIX="/usr/local"
    LIBS="-lm" ./configure --disable-tcl --enable-shared --enable-tempstore=always --prefix="$PREFIX"
    make
    make install

Post install add ``/usr/local/lib`` to library path

.. code-block:: bash

  export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

Setting up a PostgreSQL Database
--------------------------------

You need to create a database and a database user that Airflow will use to access this database.
In the example below, a database ``airflow_db`` and user  with username ``airflow_user`` with password ``airflow_pass`` will be created

.. code-block:: sql

   CREATE DATABASE airflow_db;
   CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
   GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;

   -- PostgreSQL 15 requires additional privileges:
   -- Note: Connect to the airflow_db database before running the following GRANT statement
   -- You can do this in psql with: \c airflow_db
   GRANT ALL ON SCHEMA public TO airflow_user;

.. note::

   The database must use a UTF-8 character set

You may need to update your Postgres ``pg_hba.conf`` to add the
``airflow`` user to the database access control list; and to reload
the database configuration to load your change. See
`The pg_hba.conf File <https://www.postgresql.org/docs/current/auth-pg-hba-conf.html>`__
in the Postgres documentation to learn more.

.. warning::

   When you use SQLAlchemy 1.4.0+, you need to use ``postgresql://`` as the database in the ``sql_alchemy_conn``.
   In the previous versions of SQLAlchemy it was possible to use ``postgres://``, but using it in
   SQLAlchemy 1.4.0+ results in:

   .. code-block::

      >       raise exc.NoSuchModuleError(
                  "Can't load plugin: %s:%s" % (self.group, name)
              )
      E       sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres

   If you cannot change the prefix of your URL immediately, Airflow continues to work with SQLAlchemy
   1.3 and you can downgrade SQLAlchemy, but we recommend to update the prefix.

   Details in the `SQLAlchemy Changelog <https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html#change-3687655465c25a39b968b4f5f6e9170b>`_.

We recommend using the ``psycopg2`` driver and specifying it in your SqlAlchemy connection string.

.. code-block:: text

   postgresql+psycopg2://<user>:<password>@<host>/<db>

Also note that since SqlAlchemy does not expose a way to target a specific schema in the database URI, you need to ensure schema ``public`` is in your Postgres user's search_path.

If you created a new Postgres account for Airflow:

* The default search_path for new Postgres user is: ``"$user", public``, no change is needed.

If you use a current Postgres user with custom search_path, search_path can be changed by the command:

.. code-block:: sql

   ALTER USER airflow_user SET search_path = public;

For more information regarding setup of the PostgreSQL connection, see `PostgreSQL dialect <https://docs.sqlalchemy.org/en/14/dialects/postgresql.html>`__ in SQLAlchemy documentation.

.. note::

   Airflow is known - especially in high-performance setup - to open many connections to metadata database. This might cause problems for
   Postgres resource usage, because in Postgres, each connection creates a new process and it makes Postgres resource-hungry when a lot
   of connections are opened. Therefore we recommend to use `PGBouncer <https://www.pgbouncer.org/>`_ as database proxy for all Postgres
   production installations. PGBouncer can handle connection pooling from multiple components, but also in case you have remote
   database with potentially unstable connectivity, it will make your DB connectivity much more resilient to temporary network problems.
   Example implementation of PGBouncer deployment can be found in the :doc:`helm-chart:index` where you can enable pre-configured
   PGBouncer instance with flipping a boolean flag. You can take a look at the approach we have taken there and use it as
   an inspiration, when you prepare your own Deployment, even if you do not use the Official Helm Chart.

   See also :ref:`Helm Chart production guide <production-guide:pgbouncer>`


.. note::

   For managed Postgres such as Azure Postgresql, CloudSQL, Amazon RDS, you should use
   ``keepalives_idle`` in the connection parameters and set it to less than the idle time because those
   services will close idle connections after some time of inactivity (typically 300 seconds),
   which results with error ``The error: psycopg2.operationalerror: SSL SYSCALL error: EOF detected``.
   The ``keepalive`` settings can be changed via ``sql_alchemy_connect_args`` configuration parameter
   :doc:`../configurations-ref` in ``[database]`` section. You can configure the args for example in your
   local_settings.py and the ``sql_alchemy_connect_args`` should be a full import path to the dictionary
   that stores the configuration parameters. You can read about
   `Postgres Keepalives <https://www.postgresql.org/docs/current/libpq-connect.html>`_.
   An example setup for ``keepalives`` that has been observed to fix the problem might be:

   .. code-block:: python

      keepalive_kwargs = {
          "keepalives": 1,
          "keepalives_idle": 30,
          "keepalives_interval": 5,
          "keepalives_count": 5,
      }

   Then, if it were placed in ``airflow_local_settings.py``, the config import path would be:

   .. code-block:: text

      sql_alchemy_connect_args = airflow_local_settings.keepalive_kwargs


See :ref:`Configuring local settings <set-config:configuring-local-settings>` for details on how to
configure local settings.



.. spelling:word-list::

     hba

Setting up a MySQL Database
---------------------------

You need to create a database and a database user that Airflow will use to access this database.
In the example below, a database ``airflow_db`` and user  with username ``airflow_user`` with password ``airflow_pass`` will be created

.. code-block:: sql

   CREATE DATABASE airflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'airflow_user' IDENTIFIED BY 'airflow_pass';
   GRANT ALL PRIVILEGES ON airflow_db.* TO 'airflow_user';


.. note::

   The database must use a UTF-8 character set. A small caveat that you must be aware of is that utf8 in newer versions of MySQL is really utf8mb4 which
   causes Airflow indexes to grow too large (see https://github.com/apache/airflow/pull/17603#issuecomment-901121618). Therefore as of Airflow 2.2
   all MySQL databases have ``sql_engine_collation_for_ids`` set automatically to ``utf8mb3_bin`` (unless you override it). This might
   lead to a mixture of collation ids for id fields in Airflow Database, but it has no negative consequences since all relevant IDs in Airflow use
   ASCII characters only.

We rely on more strict ANSI SQL settings for MySQL in order to have sane defaults.
Make sure to have specified ``explicit_defaults_for_timestamp=1`` option under ``[mysqld]`` section
in your ``my.cnf`` file. You can also activate these options with the ``--explicit-defaults-for-timestamp`` switch passed to ``mysqld`` executable

We recommend using the ``mysqlclient`` driver and specifying it in your SqlAlchemy connection string.

.. code-block:: text

    mysql+mysqldb://<user>:<password>@<host>[:<port>]/<dbname>

.. important::
    The integration of MySQL backend has only been validated using the ``mysqlclient`` driver
    during Apache Airflow's continuous integration (CI) process.

If you want to use other drivers visit the `MySQL Dialect <https://docs.sqlalchemy.org/en/14/dialects/mysql.html>`__  in SQLAlchemy documentation for more information regarding download
and setup of the SqlAlchemy connection.

In addition, you also should pay particular attention to MySQL's encoding. Although the ``utf8mb4`` character set is more and more popular for MySQL (actually, ``utf8mb4`` becomes default character set in MySQL8.0), using the ``utf8mb4`` encoding requires additional setting in Airflow 2+ (See more details in `#7570 <https://github.com/apache/airflow/pull/7570>`__.). If you use ``utf8mb4`` as character set, you should also set ``sql_engine_collation_for_ids=utf8mb3_bin``.

.. note::

    In strict mode, MySQL doesn't allow ``0000-00-00`` as a valid date. Then you might get errors like
    ``"Invalid default value for 'end_date'"`` in some cases (some Airflow tables use ``0000-00-00 00:00:00`` as timestamp field default value).
    To avoid this error, you could disable ``NO_ZERO_DATE`` mode on you MySQL server.
    Read https://stackoverflow.com/questions/9192027/invalid-default-value-for-create-date-timestamp-field for how to disable it.
    See `SQL Mode - NO_ZERO_DATE <https://dev.mysql.com/doc/refman/8.0/en/sql-mode.html#sqlmode_no_zero_date>`__ for more information.

MsSQL Database
--------------

.. warning::

    After `discussion <https://lists.apache.org/thread/r06j306hldg03g2my1pd4nyjxg78b3h4>`__
    and a `voting process <https://lists.apache.org/thread/pgcgmhf6560k8jbsmz8nlyoxosvltph2>`__,
    the Airflow's PMC members and Committers have reached a resolution to no longer maintain MsSQL as a supported Database Backend.

    As of Airflow 2.9.0 support of MsSQL has been removed for Airflow Database Backend.
    This does not affect the existing providers (operators and hooks), dags can still access and process data from MsSQL.
    However, further usage may throw errors making Airflow's core functionality unusable.


Migrating off MsSQL Server
~~~~~~~~~~~~~~~~~~~~~~~~~~

As with Airflow 2.9.0 the support of MSSQL has ended, a migration script can help with
Airflow version 2.7.x or 2.8.x to migrate off SQL-Server. The migration script is available in
`airflow-mssql-migration repo on GitHub <https://github.com/apache/airflow-mssql-migration>`_.

Note that the migration script is provided without support and warranty.


Other configuration options
---------------------------

There are more configuration options for configuring SQLAlchemy behavior. For details, see :ref:`reference documentation <config:database>` for ``sqlalchemy_*`` option in ``[database]`` section.

For instance, you can specify a database schema where Airflow will create its required tables. If you want Airflow to install its tables in the ``airflow`` schema of a PostgreSQL database, specify these environment variables:

.. code-block:: bash

    export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql://postgres@localhost:5432/my_database?options=-csearch_path%3Dairflow"
    export AIRFLOW__DATABASE__SQL_ALCHEMY_SCHEMA="airflow"

Note the ``search_path`` at the end of the ``SQL_ALCHEMY_CONN`` database URL.


Initialize the database
-----------------------

After configuring the database and connecting to it in Airflow configuration, you should create the database schema.

.. code-block:: bash

    airflow db migrate

Database Monitoring and Maintenance in Airflow
----------------------------------------------

Airflow extensively utilizes a relational metadata database for task scheduling and execution.
Monitoring and proper configuration of this database are crucial for optimal Airflow performance.

Key Concerns
~~~~~~~~~~~~

1. **Performance Impact**: Long or excessive queries can significantly affect Airflow's functionality.
   These may arise due to workflow specifics, lack of optimizations, or code bugs.
2. **Database Statistics**: Incorrect optimization decisions by the database engine,
   often due to outdated data statistics, can degrade performance.

Responsibilities
~~~~~~~~~~~~~~~~

The responsibilities for database monitoring and maintenance in Airflow environments vary depending on
whether you're using self-managed databases and Airflow instances or opting for managed services.

**Self-Managed Environments**:

In the setups where both the database and Airflow are self-managed, the Deployment Manager
is responsible for setting up, configuring, and maintaining the database. This includes monitoring
its performance, managing backups, periodic cleanups and ensuring its optimal operation with Airflow.

**Managed Services**:

- Managed Database Services: When using managed DB services, many maintenance tasks (like backups,
  patching, and basic monitoring) are handled by the provider. However, the Deployment Manager still
  needs to oversee the configuration of Airflow and optimize performance settings specific to their
  workflows, manages periodic cleanups and monitor their DB to ensure optimal operations with Airflow.

- Managed Airflow Services: With managed Airflow services, those service provider take responsibility
  for the configuration and maintenance of Airflow and its database. However, the Deployment Manager
  needs to collaborate with the service configuration to ensure that the sizing and workflow requirements
  are matching the sizing and configuration of the managed service.

Monitoring Aspects
~~~~~~~~~~~~~~~~~~

Regular monitoring should include:

- CPU, I/O, and memory usage.
- Query frequency and number.
- Identification and logging of slow or long-running queries.
- Detection of inefficient query execution plans.
- Analysis of disk swap versus memory usage and cache swapping frequency.

Tools and Strategies
~~~~~~~~~~~~~~~~~~~~

- Airflow doesn't provide direct tooling for database monitoring.
- Use server-side monitoring and logging to obtain metrics.
- Enable tracking of long-running queries based on defined thresholds.
- Regularly run house-keeping tasks (like ``ANALYZE`` SQL command) for maintenance.

Database Cleaning Tools
~~~~~~~~~~~~~~~~~~~~~~~

- **Airflow DB Clean Command**: Utilize the ``airflow db clean`` command to help manage and clean
  up your database.
- **Python Methods in ``airflow.utils.db_cleanup``**: This module provides additional Python methods for
  database cleanup and maintenance, offering more fine-grained control and customization for specific needs.

Recommendations
~~~~~~~~~~~~~~~

- **Proactive Monitoring**: Implement monitoring and logging in production without significantly
  impacting performance.
- **Database-Specific Guidance**: Consult the chosen database's documentation for specific monitoring
  setup instructions.
- **Managed Database Services**: Check if automatic maintenance tasks are available with your
  database provider.

SQLAlchemy Logging
~~~~~~~~~~~~~~~~~~

For detailed query analysis, enable SQLAlchemy client logging (``echo=True`` in SQLAlchemy
engine configuration).

- This method is more intrusive and can affect Airflow's client-side performance.
- It generates a lot of logs, especially in a busy Airflow environment.
- Suitable for non-production environments like staging systems.

You can do it with ``echo=True`` as sqlalchemy engine configuration as explained in the
`SQLAlchemy logging documentation <https://docs.sqlalchemy.org/en/14/core/engines.html#configuring-logging>`_.

Use :ref:`config:database__sql_alchemy_engine_args` configuration parameter to set echo arg to True.

Caution
~~~~~~~

- Be mindful of the impact on Airflow's performance and system resources when enabling extensive logging.
- Prefer server-side monitoring over client-side logging for production environments to minimize
  performance interference.

What's next?
------------

By default, Airflow uses ``LocalExecutor``. You should consider
configuring a different :doc:`executor </core-concepts/executor/index>` for better performance.
