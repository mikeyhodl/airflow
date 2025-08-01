# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

import logging
import sys
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, Response, status
from pydantic import BaseModel, JsonValue, StringConstraints
from sqlalchemy import delete
from sqlalchemy.sql.selectable import Select

from airflow.api_fastapi.common.db.common import SessionDep
from airflow.api_fastapi.execution_api.datamodels.xcom import (
    XComResponse,
    XComSequenceIndexResponse,
    XComSequenceSliceResponse,
)
from airflow.api_fastapi.execution_api.deps import JWTBearerDep
from airflow.models.taskmap import TaskMap
from airflow.models.xcom import XComModel
from airflow.utils.db import get_query_count


async def has_xcom_access(
    dag_id: str,
    run_id: str,
    task_id: str,
    xcom_key: Annotated[str, Path(alias="key")],
    request: Request,
    token=JWTBearerDep,
) -> bool:
    """Check if the task has access to the XCom."""
    # TODO: Placeholder for actual implementation

    write = request.method not in {"GET", "HEAD", "OPTIONS"}

    log.debug(
        "Checking %s XCom access for xcom from TaskInstance with key '%s' to XCom '%s'",
        "write" if write else "read",
        token.id,
        xcom_key,
    )
    return True


router = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Task does not have access to the XCom"},
        status.HTTP_404_NOT_FOUND: {"description": "XCom not found"},
    },
    dependencies=[Depends(has_xcom_access)],
)

log = logging.getLogger(__name__)


async def xcom_query(
    dag_id: str,
    run_id: str,
    task_id: str,
    key: str,
    session: SessionDep,
    map_index: Annotated[int | None, Query()] = None,
) -> Select:
    query = XComModel.get_many(
        run_id=run_id,
        key=key,
        task_ids=task_id,
        dag_ids=dag_id,
        map_indexes=map_index,
        session=session,
    )
    return query


@router.head(
    "/{dag_id}/{run_id}/{task_id}/{key}",
    responses={
        status.HTTP_200_OK: {
            "description": "Metadata about the number of matching XCom values",
            "headers": {
                "Content-Range": {
                    "schema": {"pattern": r"^map_indexes \d+$"},
                    "description": "The number of (mapped) XCom values found for this task.",
                },
            },
        },
    },
    description="Returns the count of mapped XCom values found in the `Content-Range` response header",
)
def head_xcom(
    response: Response,
    session: SessionDep,
    xcom_query: Annotated[Select, Depends(xcom_query)],
    map_index: Annotated[int | None, Query()] = None,
) -> None:
    """Get the count of XComs from database - not other XCom Backends."""
    if map_index is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"reason": "invalid_request", "message": "Cannot specify map_index in a HEAD request"},
        )

    count = get_query_count(xcom_query, session=session)
    # Tell the caller how many items in this query. We define a custom range unit (HTTP spec only defines
    # "bytes" but we can add our own)
    response.headers["Content-Range"] = f"map_indexes {count}"


class GetXcomFilterParams(BaseModel):
    """Class to house the params that can optionally be set for Get XCom."""

    map_index: int = -1
    include_prior_dates: bool = False
    offset: int | None = None


@router.get(
    "/{dag_id}/{run_id}/{task_id}/{key}",
    description="Get a single XCom Value",
)
def get_xcom(
    dag_id: str,
    run_id: str,
    task_id: str,
    key: Annotated[str, StringConstraints(min_length=1)],
    session: SessionDep,
    params: Annotated[GetXcomFilterParams, Query()],
) -> XComResponse:
    """Get an Airflow XCom from database - not other XCom Backends."""
    xcom_query = XComModel.get_many(
        run_id=run_id,
        key=key,
        task_ids=task_id,
        dag_ids=dag_id,
        include_prior_dates=params.include_prior_dates,
        session=session,
    )
    if params.offset is not None:
        xcom_query = xcom_query.filter(XComModel.value.is_not(None)).order_by(None)
        if params.offset >= 0:
            xcom_query = xcom_query.order_by(XComModel.map_index.asc()).offset(params.offset)
        else:
            xcom_query = xcom_query.order_by(XComModel.map_index.desc()).offset(-1 - params.offset)
    else:
        xcom_query = xcom_query.filter(XComModel.map_index == params.map_index)

    # We use `BaseXCom.get_many` to fetch XComs directly from the database, bypassing the XCom Backend.
    # This avoids deserialization via the backend (e.g., from a remote storage like S3) and instead
    # retrieves the raw serialized value from the database. By not relying on `XCom.get_many` or `XCom.get_one`
    # (which automatically deserializes using the backend), we avoid potential
    # performance hits from retrieving large data files into the API server.
    result = xcom_query.limit(1).first()
    if result is None:
        if params.offset is None:
            message = (
                f"XCom with {key=} map_index={params.map_index} not found for "
                f"task {task_id!r} in DAG run {run_id!r} of {dag_id!r}"
            )
        else:
            message = (
                f"XCom with {key=} offset={params.offset} not found for "
                f"task {task_id!r} in DAG run {run_id!r} of {dag_id!r}"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"reason": "not_found", "message": message},
        )

    return XComResponse(key=key, value=result.value)


@router.get(
    "/{dag_id}/{run_id}/{task_id}/{key}/item/{offset}",
    description="Get a single XCom value from a mapped task by sequence index",
)
def get_mapped_xcom_by_index(
    dag_id: str,
    run_id: str,
    task_id: str,
    key: str,
    offset: int,
    session: SessionDep,
) -> XComSequenceIndexResponse:
    xcom_query = XComModel.get_many(
        run_id=run_id,
        key=key,
        task_ids=task_id,
        dag_ids=dag_id,
        session=session,
    )
    xcom_query = xcom_query.order_by(None)
    if offset >= 0:
        xcom_query = xcom_query.order_by(XComModel.map_index.asc()).offset(offset)
    else:
        xcom_query = xcom_query.order_by(XComModel.map_index.desc()).offset(-1 - offset)

    if (result := xcom_query.limit(1).first()) is None:
        message = (
            f"XCom with {key=} {offset=} not found for task {task_id!r} in DAG run {run_id!r} of {dag_id!r}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"reason": "not_found", "message": message},
        )
    return XComSequenceIndexResponse(result.value)


class GetXComSliceFilterParams(BaseModel):
    """Class to house slice params."""

    start: int | None = None
    stop: int | None = None
    step: int | None = None
    include_prior_dates: bool = False


@router.get(
    "/{dag_id}/{run_id}/{task_id}/{key}/slice",
    description="Get XCom values from a mapped task by sequence slice",
)
def get_mapped_xcom_by_slice(
    dag_id: str,
    run_id: str,
    task_id: str,
    key: str,
    params: Annotated[GetXComSliceFilterParams, Query()],
    session: SessionDep,
) -> XComSequenceSliceResponse:
    query = XComModel.get_many(
        run_id=run_id,
        key=key,
        task_ids=task_id,
        dag_ids=dag_id,
        include_prior_dates=params.include_prior_dates,
        session=session,
    )
    query = query.order_by(None)

    step = params.step or 1

    # We want to optimize negative slicing (e.g. seq[-10:]) by not doing an
    # additional COUNT query if possible. This is possible unless both start and
    # stop are explicitly given and have different signs.
    if (start := params.start) is None:
        if (stop := params.stop) is None:
            if step >= 0:
                query = query.order_by(XComModel.map_index.asc())
            else:
                query = query.order_by(XComModel.map_index.desc())
                step = -step
        elif stop >= 0:
            query = query.order_by(XComModel.map_index.asc())
            if step >= 0:
                query = query.limit(stop)
            else:
                query = query.offset(stop + 1)
        else:
            query = query.order_by(XComModel.map_index.desc())
            step = -step
            if step > 0:
                query = query.limit(-stop - 1)
            else:
                query = query.offset(-stop)
    elif start >= 0:
        query = query.order_by(XComModel.map_index.asc())
        if (stop := params.stop) is None:
            if step >= 0:
                query = query.offset(start)
            else:
                query = query.limit(start + 1)
        else:
            if stop < 0:
                stop += get_query_count(query, session=session)
            if step >= 0:
                query = query.slice(start, stop)
            else:
                query = query.slice(stop + 1, start + 1)
    else:
        query = query.order_by(XComModel.map_index.desc())
        step = -step
        if (stop := params.stop) is None:
            if step > 0:
                query = query.offset(-start - 1)
            else:
                query = query.limit(-start)
        else:
            if stop >= 0:
                stop -= get_query_count(query, session=session)
            if step > 0:
                query = query.slice(-1 - start, -1 - stop)
            else:
                query = query.slice(-stop, -start)

    values = [row.value for row in query.with_entities(XComModel.value)]
    if step != 1:
        values = values[::step]
    return XComSequenceSliceResponse(values)


if sys.version_info < (3, 12):
    # zmievsa/cadwyn#262
    # Setting this to "Any" doesn't have any impact on the API as it has to be parsed as valid JSON regardless
    JsonValue = Any  # type: ignore [misc]


# TODO: once we have JWT tokens, then remove dag_id/run_id/task_id from the URL and just use the info in
# the token
@router.post(
    "/{dag_id}/{run_id}/{task_id}/{key}",
    status_code=status.HTTP_201_CREATED,
)
def set_xcom(
    dag_id: str,
    run_id: str,
    task_id: str,
    key: Annotated[str, StringConstraints(min_length=1)],
    value: Annotated[
        JsonValue,
        Body(
            description="A JSON-formatted string representing the value to set for the XCom.",
            openapi_examples={
                "simple_value": {
                    "summary": "Simple value",
                    "value": '"value1"',
                },
                "dict_value": {
                    "summary": "Dictionary value",
                    "value": '{"key2": "value2"}',
                },
                "list_value": {
                    "summary": "List value",
                    "value": '["value1"]',
                },
            },
        ),
    ],
    session: SessionDep,
    map_index: Annotated[int, Query()] = -1,
    mapped_length: Annotated[
        int | None, Query(description="Number of mapped tasks this value expands into")
    ] = None,
):
    """Set an Airflow XCom."""
    from airflow.configuration import conf

    # Validate that the provided key is not empty
    # XCom keys must be non-empty strings to ensure proper data retrieval and avoid ambiguity.
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "reason": "invalid_key",
                "message": "XCom key must be a non-empty string.",
            },
        )

    if mapped_length is not None:
        task_map = TaskMap(
            dag_id=dag_id,
            task_id=task_id,
            run_id=run_id,
            map_index=map_index,
            length=mapped_length,
            keys=None,
        )
        max_map_length = conf.getint("core", "max_map_length", fallback=1024)
        if task_map.length > max_map_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "reason": "unmappable_return_value_length",
                    "message": "pushed value is too large to map as a downstream's dependency",
                },
            )
        session.merge(task_map)

    # else:
    # TODO: Can/should we check if a client _hasn't_ provided this for an upstream of a mapped task? That
    # means loading the serialized dag and that seems like a relatively costly operation for minimal benefit
    # (the mapped task would fail in a moment as it can't be expanded anyway.)
    from airflow.models.dagrun import DagRun

    if not run_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Run with ID: `{run_id}` was not found")

    dag_run_id = session.query(DagRun.id).filter_by(dag_id=dag_id, run_id=run_id).scalar()
    if dag_run_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"DAG run not found on DAG {dag_id} with ID {run_id}")

    # Remove duplicate XComs and insert a new one.
    session.execute(
        delete(XComModel).where(
            XComModel.key == key,
            XComModel.run_id == run_id,
            XComModel.task_id == task_id,
            XComModel.dag_id == dag_id,
            XComModel.map_index == map_index,
        )
    )

    try:
        # We expect serialised value from the caller - sdk, do not serialise in here
        new = XComModel(
            dag_run_id=dag_run_id,
            key=key,
            value=value,
            run_id=run_id,
            task_id=task_id,
            dag_id=dag_id,
            map_index=map_index,
        )
        session.add(new)
        session.flush()
    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "reason": "invalid_format",
                "message": f"XCom value is not a valid JSON: {e}",
            },
        )

    return {"message": "XCom successfully set"}


@router.delete(
    "/{dag_id}/{run_id}/{task_id}/{key}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "XCom not found"}},
    description="Delete a single XCom Value",
)
def delete_xcom(
    session: SessionDep,
    dag_id: str,
    run_id: str,
    task_id: str,
    key: str,
    map_index: Annotated[int, Query()] = -1,
):
    """Delete a single XCom Value."""
    query = delete(XComModel).where(
        XComModel.key == key,
        XComModel.run_id == run_id,
        XComModel.task_id == task_id,
        XComModel.dag_id == dag_id,
        XComModel.map_index == map_index,
    )
    session.execute(query)
    session.commit()
    return {"message": f"XCom with key: {key} successfully deleted."}
