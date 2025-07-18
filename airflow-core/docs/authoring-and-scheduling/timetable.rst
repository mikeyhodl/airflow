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


Timetables
==========

For a DAG with a time-based schedule (as opposed to event-driven), the DAG's internal "timetable"
drives scheduling.  The timetable also determines the data interval and the logical date of
each run created for the DAG.

Dags scheduled with a cron expression or ``timedelta`` object are
internally converted to always use a timetable.

If a cron expression or ``timedelta`` is sufficient for your use case, you don't need
to worry about writing a custom timetable because Airflow has default timetables that handle those cases.
But for more complicated scheduling requirements,
you can create your own timetable class and pass that to the DAG's ``schedule`` argument.

Some examples of when custom timetable implementations are useful:

* Task runs that occur at different times each day. For example, an astronomer might find it
  useful to run a task at dawn to process data collected from the previous
  night-time period.
* Schedules that don't follow the Gregorian calendar. For example, create a run for
  each month in the `Traditional Chinese Calendar`_. This is conceptually
  similar to the sunrise case, but for a different time scale.
* Rolling windows, or overlapping data intervals. For example, you might want to
  have a run each day, but make each run cover the period of the previous seven
  days. It is possible to hack this with a cron expression, but a custom data
  interval provides a more natural representation.
* Data intervals with "holes" between intervals instead of a continuous interval, as both the cron
  expression and ``timedelta`` schedules represent continuous intervals. See :ref:`data-interval`.

.. _`Traditional Chinese Calendar`: https://en.wikipedia.org/wiki/Chinese_calendar

Airflow allows you to write custom timetables in plugins and used by
dags. You can find an example demonstrating a custom timetable in the
:doc:`/howto/timetable` how-to guide.

.. note::

    As a general rule, always access Variables, Connections, or anything else that needs access to
    the database as late as possible in your code. See :ref:`best_practices/timetables`
    for more best practices to follow.

Built-in Timetables
-------------------

Airflow comes with several common timetables built-in to cover the most common use cases. Additional timetables
may be available in plugins.

.. _DeltaTriggerTimetable:

DeltaTriggerTimetable
^^^^^^^^^^^^^^^^^^^^^

A timetable that accepts a :class:`datetime.timedelta` or ``dateutil.relativedelta.relativedelta``, and runs
the DAG once a delta passes.

.. seealso:: `Differences between "trigger" and "data interval" timetables`_

.. code-block:: python

    from datetime import timedelta

    from airflow.timetables.trigger import DeltaTriggerTimetable


    @dag(schedule=DeltaTriggerTimetable(timedelta(days=7)), ...)  # Once every week.
    def example_dag():
        pass

You can also provide a static data interval to the timetable. The optional ``interval`` argument also
should be a :class:`datetime.timedelta` or ``dateutil.relativedelta.relativedelta``. When using these
arguments, a triggered DAG run's data interval spans the specified duration, and *ends* with the trigger time.

.. code-block:: python

    from datetime import UTC, datetime, timedelta

    from dateutil.relativedelta import relativedelta, FR

    from airflow.timetables.trigger import DeltaTriggerTimetable


    @dag(
        # Runs every Friday at 18:00 to cover the work week.
        schedule=DeltaTriggerTimetable(
            relativedelta(weekday=FR(), hour=18),
            interval=timedelta(days=4, hours=9),
        ),
        start_date=datetime(2025, 1, 3, 18, tzinfo=UTC),
        ...,
    )
    def example_dag():
        pass


.. _CronTriggerTimetable:

CronTriggerTimetable
^^^^^^^^^^^^^^^^^^^^

A timetable that accepts a cron expression, and triggers DAG runs according to it.

.. seealso:: `Differences between "trigger" and "data interval" timetables`_

.. code-block:: python

    from airflow.timetables.trigger import CronTriggerTimetable


    @dag(schedule=CronTriggerTimetable("0 1 * * 3", timezone="UTC"), ...)  # At 01:00 on Wednesday
    def example_dag():
        pass

You can also provide a static data interval to the timetable. The optional ``interval`` argument
must be a :class:`datetime.timedelta` or ``dateutil.relativedelta.relativedelta``. When using these arguments, a triggered DAG run's data interval spans the specified duration, and *ends* with the trigger time.

.. code-block:: python

    from datetime import timedelta

    from airflow.timetables.trigger import CronTriggerTimetable


    @dag(
        # Runs every Friday at 18:00 to cover the work week (9:00 Monday to 18:00 Friday).
        schedule=CronTriggerTimetable(
            "0 18 * * 5",
            timezone="UTC",
            interval=timedelta(days=4, hours=9),
        ),
        ...,
    )
    def example_dag():
        pass


.. _MultipleCronTriggerTimetable:

MultipleCronTriggerTimetable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is similar to CronTriggerTimetable_ except it takes multiple cron expressions. A DAG run is scheduled whenever any of the expressions matches the time. It is particularly useful when the desired schedule cannot be expressed by one single cron expression.

.. code-block:: python

    from airflow.timetables.trigger import MultipleCronTriggerTimetable


    # At 1:10 and 2:40 each day.
    @dag(schedule=MultipleCronTriggerTimetable("10 1 * * *", "40 2 * * *", timezone="UTC"), ...)
    def example_dag():
        pass

The same optional ``interval`` argument as CronTriggerTimetable_ is also available.

.. code-block:: python

    from datetime import timedelta

    from airflow.timetables.trigger import MultipleCronTriggerTimetable


    @dag(
        schedule=MultipleCronTriggerTimetable(
            "10 1 * * *",
            "40 2 * * *",
            timezone="UTC",
            interval=timedelta(hours=1),
        ),
        ...,
    )
    def example_dag():
        pass


.. _DeltaDataIntervalTimetable:

DeltaDataIntervalTimetable
^^^^^^^^^^^^^^^^^^^^^^^^^^

A timetable that schedules data intervals with a time delta. You can select it by providing a
:class:`datetime.timedelta` or ``dateutil.relativedelta.relativedelta`` to the ``schedule`` parameter of a DAG.

This timetable focuses on the data interval value and does not necessarily align execution dates with
arbitrary bounds, such as the start of day or of hour.

.. seealso:: `Differences between the cron and delta data interval timetables`_

.. code-block:: python

    @dag(schedule=datetime.timedelta(minutes=30))
    def example_dag():
        pass

.. _CronDataIntervalTimetable:

CronDataIntervalTimetable
^^^^^^^^^^^^^^^^^^^^^^^^^

A timetable that accepts a cron expression, creates data intervals according to the interval between each cron
trigger points, and triggers a DAG run at the end of each data interval.

.. seealso:: `Differences between "trigger" and "data interval" timetables`_
.. seealso:: `Differences between the cron and delta data interval timetables`_

Select this timetable by providing a valid cron expression as a string to the ``schedule``
parameter of a DAG, as described in the :doc:`../core-concepts/dags` documentation.

.. code-block:: python

    @dag(schedule="0 1 * * 3")  # At 01:00 on Wednesday.
    def example_dag():
        pass

EventsTimetable
^^^^^^^^^^^^^^^

Pass a list of ``datetime``\s for the DAG to run after. This can be useful for timing based on sporting
events, planned communication campaigns, and other schedules that are arbitrary and irregular, but predictable.

The list of events must be finite and of reasonable size as it must be loaded every time the DAG is parsed. Optionally, use
the ``restrict_to_events`` flag to force manual runs of the DAG that use the time of the most recent, or very
first, event for the data interval. Otherwise, manual runs begin with a ``data_interval_start`` and
``data_interval_end`` equal to the time at which the manual run started. You can also name the set of events using the
``description`` parameter, which will be displayed in the Airflow UI.

.. code-block:: python

    from airflow.timetables.events import EventsTimetable


    @dag(
        schedule=EventsTimetable(
            event_dates=[
                pendulum.datetime(2022, 4, 5, 8, 27, tz="America/Chicago"),
                pendulum.datetime(2022, 4, 17, 8, 27, tz="America/Chicago"),
                pendulum.datetime(2022, 4, 22, 20, 50, tz="America/Chicago"),
            ],
            description="My Team's Baseball Games",
            restrict_to_events=False,
        ),
        ...,
    )
    def example_dag():
        pass

.. _asset-timetable-section:

Asset event based scheduling with time based scheduling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Combining conditional asset expressions with time-based schedules enhances scheduling flexibility.

The ``AssetOrTimeSchedule`` is a specialized timetable that allows for the scheduling of dags based on both time-based schedules and asset events. It also facilitates the creation of both scheduled runs, as per traditional timetables, and asset-triggered runs, which operate independently.

This feature is particularly useful in scenarios where a DAG needs to run on asset updates and also at periodic intervals. It ensures that the workflow remains responsive to data changes and consistently runs regular checks or updates.

Here's an example of a DAG using ``AssetOrTimeSchedule``:

.. code-block:: python

    from airflow.timetables.assets import AssetOrTimeSchedule
    from airflow.timetables.trigger import CronTriggerTimetable


    @dag(
        schedule=AssetOrTimeSchedule(
            timetable=CronTriggerTimetable("0 1 * * 3", timezone="UTC"), assets=(dag1_asset & dag2_asset)
        )
        # Additional arguments here, replace this comment with actual arguments
    )
    def example_dag():
        # DAG tasks go here
        pass



Timetables comparisons
----------------------

.. _Differences between "trigger" and "data interval" timetables:

Differences between "trigger" and "data interval" timetables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Airflow has two sets of timetables for cron and delta schedules:

* CronTriggerTimetable_ and CronDataIntervalTimetable_ both accept a cron expression.
* DeltaTriggerTimetable_ and DeltaDataIntervalTimetable_ both accept a timedelta or relativedelta.

- A trigger timetable (CronTriggerTimetable_ or DeltaTriggerTimetable_) does not address the concept of *data interval*, while a "data interval" one (CronDataIntervalTimetable_ or DeltaDataIntervalTimetable_) does.
- The timestamp in the ``run_id``, the ``logical_date`` of the two timetable kinds are defined differently based on how they handle the data interval, as described in :ref:`timetables_run_id_logical_date`.

Whether taking care of *Data Interval*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A trigger timetable *does not* include *data interval*. This means that the value of ``data_interval_start``
and ``data_interval_end`` are the same; the time when a DAG run is triggered.

For a data interval timetable, the value of ``data_interval_start`` and ``data_interval_end`` are different.
``data_interval_end`` is the time when a DAG run is triggered, while ``data_interval_start`` is the start of the interval.

*Catchup* behavior
^^^^^^^^^^^^^^^^^^

By default, ``catchup`` is set to ``False``. This prevents running unnecessary dags in the following scenarios:

- If you create a new DAG with a start date in the past, and don't want to run dags for the past. If ``catchup`` is ``True``, Airflow runs all dags that would have run in that time interval.
- If you pause an existing DAG, and then restart it at a later date, ``catchup`` being ``False`` means that Airflow does not run the dags that would have run during the paused period.

In these scenarios, the ``logical_date`` in the ``run_id`` are based on how how the timetable handles the data
interval.

You can change the default ``catchup`` behavior using the Airflow config ``[scheduler] catchup_by_default``.

See :ref:`dag-catchup` for more information about how DAG runs are triggered when using ``catchup``.

.. _timetables_run_id_logical_date:

The time when a DAG run is triggered
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both trigger and data interval timetables trigger DAG runs at the same time. However, the timestamp for the
``run_id`` is different for each. This is because ``run_id`` is based on ``logical_date``.

For example, suppose there is a cron expression ``@daily`` or ``0 0 * * *``, which is scheduled to run at 12AM every day. If you enable dags using the two timetables at 3PM on January
31st,

- `CronTriggerTimetable`_ creates a new DAG run at 12AM on February 1st. The ``run_id`` timestamp is midnight, on February 1st.
- `CronDataIntervalTimetable`_ immediately creates a new DAG run, because a DAG run for the daily time interval beginning at 12AM on January 31st did not occur yet. The ``run_id`` timestamp is midnight, on January 31st, since that is the beginning of the data interval.

The following is another example showing the difference in the case of skipping DAG runs:

Suppose there are two running dags with a cron expression ``@daily`` or ``0 0 * * *`` that use the two different timetables. If you pause the dags at 3PM on January 31st and re-enable them at 3PM on February 2nd,

- `CronTriggerTimetable`_ skips the DAG runs that were supposed to trigger on February 1st and 2nd. The next DAG run will be triggered at 12AM on February 3rd.
- `CronDataIntervalTimetable`_ skips the DAG runs that were supposed to trigger on February 1st only. A DAG run for February 2nd is immediately triggered after you re-enable the DAG.

In these examples, you see how a trigger timetable creates DAG runs more intuitively and similar to what
people expect a workflow to behave, while a data interval timetable is designed heavily around the data
interval it processes, and does not reflect a workflow's own properties.


.. _Differences between the cron and delta data interval timetables:

Differences between the cron and delta data interval timetables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Choosing between `DeltaDataIntervalTimetable`_ and `CronDataIntervalTimetable`_ depends on your use case.
If you enable a DAG at 01:05 on February 1st, the following table summarizes the DAG runs created and the
data interval that they cover, depending on 3 arguments: ``schedule``, ``start_date`` and ``catchup``.

.. list-table::
   :header-rows: 1

   * - ``schedule``
     - ``start_date``
     - ``catchup``
     - Intervals covered
     - Remarks

   * - ``*/30 * * * *``
     - ``year-02-01``
     - ``True``
     - * 00:00 - 00:30
       * 00:30 - 01:00
     - Same behavior than using the timedelta object.

   * - ``*/30 * * * *``
     - ``year-02-01``
     - ``False``
     - * 00:30 - 01:00
     -

   * - ``*/30 * * * *``
     - ``year-02-01 00:10``
     - ``True``
     - * 00:30 - 01:00
     - Interval 00:00 - 00:30 is not after the start date, and so is skipped.

   * - ``*/30 * * * *``
     - ``year-02-01 00:10``
     - ``False``
     - * 00:30 - 01:00
     - Whatever the start date, the data intervals are aligned with hour/day/etc. boundaries.

   * - ``datetime.timedelta(minutes=30)``
     - ``year-02-01``
     - ``True``
     - * 00:00 - 00:30
       * 00:30 - 01:00
     - Same behavior than using the cron expression.

   * - ``datetime.timedelta(minutes=30)``
     - ``year-02-01``
     - ``False``
     - * 00:35 - 01:05
     - Interval is not aligned with start date but with the current time.

   * - ``datetime.timedelta(minutes=30)``
     - ``year-02-01 00:10``
     - ``True``
     - * 00:10 - 00:40
     - Interval is aligned with start date. Next one will be triggered in 5 minutes covering 00:40 - 01:10.

   * - ``datetime.timedelta(minutes=30)``
     - ``year-02-01 00:10``
     - ``False``
     - * 00:35 - 01:05
     - Interval is aligned with current time. Next run will be triggered in 30 minutes.
