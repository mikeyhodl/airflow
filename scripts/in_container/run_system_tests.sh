#!/usr/bin/env bash
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

#
# Bash coherence settings (error on exit, complain for undefined vars, error when pipe fails)
set -euo pipefail

IN_CONTAINER_DIR=$(cd "$(dirname "$0")" || exit 1; pwd)

# shellcheck source=scripts/in_container/_in_container_utils.sh
. "${IN_CONTAINER_DIR}/_in_container_utils.sh"

in_container_set_colors
in_container_basic_check
in_container_script_start

# any argument received is overriding the default nose execution arguments:
PYTEST_ARGS=( "$@" )

echo
echo "Starting system tests with those pytest arguments: --system ${PYTEST_ARGS[*]}"
echo
set +e

pytest --system "${PYTEST_ARGS[@]}"

RES=$?

set +x
if [[ "${RES}" == "0" && ( ${GITHUB_ACTIONS=} == "true" || ${GITHUB_ACTIONS} == "True" ) ]]; then
    echo "All tests successful"
fi

if [[ ${GITHUB_ACTIONS=} == "true" || ${GITHUB_ACTIONS} == "True" ]]; then
    dump_airflow_logs
fi

exit "${RES}"
