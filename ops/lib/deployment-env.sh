#!/usr/bin/env bash
# Shared Compose configuration for ops and offline installers (Bash 4+).
# Read dotenv as data. Never execute environment files as shell scripts.

radp_config_die() { printf '[radp-config][ERROR] %s\n' "$*" >&2; return 1; }

radp_config_read_file() {
    local path="$1" line key value
    [[ -f "$path" && ! -L "$path" ]] || { radp_config_die "Missing or symlinked configuration: $path"; return 1; }
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
        [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]] || { radp_config_die "Invalid environment assignment in $path"; return 1; }
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        # dotenv-compatible enclosing quotes; no expansion or command substitution.
        if [[ "$value" == \"*\" || "$value" == \'*\' ]]; then
            value="${value:1:${#value}-2}"
        fi
        export "$key=$value"
    done < "$path"
}

radp_config_activate() {
    local root="$1" host authority
    radp_config_read_file "$root/.env" || return 1
    radp_config_read_file "$root/.env.compose" || return 1
    # Required for Ofelia's project-label filter; not derived by Compose v1.
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-radp}"
    export COMPOSE_PROJECT_NAME
    RADP_COMPOSE_FILES=(-f "$root/docker-compose.yml")
    case "${DEPLOY_ENVIRONMENT:-test}" in
        test|development|local)
            ;;
        production)
            [[ -f "$root/docker-compose.production.yml" ]] || { radp_config_die 'Production Compose overlay missing'; return 1; }
            [[ -n "${DEPLOY_RA_HOST_IP:-}" ]] || { radp_config_die 'DEPLOY_RA_HOST_IP is required for production'; return 1; }
            # Docker extra_hosts requires a literal IP; enforce IPv4 for this
            # deployment contract rather than allowing an unresolved DNS name.
            [[ "$DEPLOY_RA_HOST_IP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]] || { radp_config_die 'DEPLOY_RA_HOST_IP must be an IPv4 address'; return 1; }
            local octet
            local -a octets
            IFS=. read -r -a octets <<< "$DEPLOY_RA_HOST_IP"
            for octet in "${octets[@]}"; do
                (( 10#$octet <= 255 )) || { radp_config_die 'DEPLOY_RA_HOST_IP has an out-of-range octet'; return 1; }
            done
            [[ "${RADP_REMOTE_RA__BASE_URL:-}" =~ ^https?://([^/]+)(/|$) ]] || { radp_config_die 'Production RA base URL must begin with http:// or https://'; return 1; }
            authority="${BASH_REMATCH[1]}"
            # The hostname cannot differ from the application URL by configuration.
            host="${authority%%:*}"
            [[ "$host" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || { radp_config_die 'Invalid remote RA hostname'; return 1; }
            DEPLOY_RA_HOSTNAME="$host"
            export DEPLOY_RA_HOSTNAME
            RADP_COMPOSE_FILES+=(-f "$root/docker-compose.production.yml")
            ;;
        *)
            radp_config_die "DEPLOY_ENVIRONMENT must be test, local, development, or production"; return 1
            ;;
    esac
}
