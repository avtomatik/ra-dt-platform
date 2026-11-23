#!/bin/sh
set -eu

: "${DEPLOY_CONTAINER_GID:?Set DEPLOY_CONTAINER_GID}"
: "${DEPLOY_CONTAINER_UID:?Set DEPLOY_CONTAINER_UID}"
: "${DEPLOY_CONTAINER_USER:?Set DEPLOY_CONTAINER_USER}"

if ! [ "${DEPLOY_CONTAINER_GID}" -gt 0 ] ||
    ! [ "${DEPLOY_CONTAINER_UID}" -gt 0 ]; then
    echo "Container GID and UID must be positive integers" >&2
    exit 1
fi

###############################################################################
# Create or validate the required group.
###############################################################################
if getent group "${DEPLOY_CONTAINER_USER}" >/dev/null; then
    actual_gid="$(getent group "${DEPLOY_CONTAINER_USER}" | cut -d: -f3)"

    if [ "${actual_gid}" != "${DEPLOY_CONTAINER_GID}" ]; then
        echo "Container group identity mismatch" >&2
        exit 1
    fi
else
    groupadd \
        --gid "${DEPLOY_CONTAINER_GID}" \
        "${DEPLOY_CONTAINER_USER}"
fi

###############################################################################
# Create or validate the required user.
###############################################################################
if id "${DEPLOY_CONTAINER_USER}" >/dev/null 2>&1; then
    if [ "$(id -u "${DEPLOY_CONTAINER_USER}")" != "${DEPLOY_CONTAINER_UID}" ] ||
        [ "$(id -g "${DEPLOY_CONTAINER_USER}")" != "${DEPLOY_CONTAINER_GID}" ]; then
        echo "Container user identity mismatch" >&2
        exit 1
    fi
else
    useradd \
        --gid "${DEPLOY_CONTAINER_GID}" \
        --uid "${DEPLOY_CONTAINER_UID}" \
        --create-home \
        --shell /bin/bash \
        "${DEPLOY_CONTAINER_USER}"
fi

HOME="$(getent passwd "${DEPLOY_CONTAINER_USER}" | cut -d: -f6)"
export HOME
export USER="${DEPLOY_CONTAINER_USER}"
export LOGNAME="${DEPLOY_CONTAINER_USER}"

mkdir -p /app/data/exports /app/logs

chown "${DEPLOY_CONTAINER_UID}:${DEPLOY_CONTAINER_GID}" \
    /app/data \
    /app/data/exports \
    /app/logs

###############################################################################
# Verify runtime directory access without modifying host ownership.
###############################################################################
gosu "${DEPLOY_CONTAINER_USER}" sh -c '
    test -d "$HOME" &&
    test -w "$HOME" &&
    test -w /app/logs &&
    test -w /app/data/exports
'

###############################################################################
# Replace the privileged entrypoint with the unprivileged application.
###############################################################################
exec gosu "${DEPLOY_CONTAINER_USER}" "$@"
