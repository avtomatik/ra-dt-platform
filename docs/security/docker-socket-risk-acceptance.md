# Risk acceptance: Ofelia access to the Docker socket

**Status:** proposed acceptance; requires approval by the system/service owner before production use.

## Finding

The Compose service `scheduler` mounts `/var/run/docker.sock` and starts Ofelia in Docker-discovery mode. This is required by the current design because Ofelia discovers the `platform` container and executes the synchronization job declared in its labels.

The mount suffix `:ro` protects the mounted filesystem entry from writes through that mount. It does **not** make requests sent to the Docker API read-only. A process that can use the Docker socket may be able to create or control containers and thereby gain extensive control over the Docker host.

## Business and operational justification

The current deployment uses Ofelia to run a scheduled `radp sync run` command without embedding a scheduler in the RADP application. Keeping this mechanism avoids an unrelated scheduler redesign in the current stabilization release. In an air-gapped production network, the lack of direct internet connectivity reduces some external attack paths, but does not remove the risk from a compromised application/container, malicious or tampered image, or an authorized insider.

## Required compensating controls

- Restrict interactive and administrative access to the Docker host to authorized operators; protect and audit privileged access.
- Do not expose the Docker API over an unauthenticated TCP endpoint.
- Use trusted, reviewed, version-pinned images; avoid mutable `latest` tags in a production release and record image digests in the release manifest.
- Keep the scheduler service dedicated to the required Ofelia job and review container labels/job commands as part of each change.
- Do not mount the Docker socket into the RADP `platform` or database containers.
- Keep PostgreSQL on the private Compose network unless a separately approved operational requirement justifies host publication.
- Reassess this acceptance if the deployment gains network connectivity, additional containers/jobs, new image sources, or a different threat model.

## Residual risk and decision

Residual risk remains **high impact** because Docker socket access can provide control over the host's container workload. Air-gapping is a mitigating environmental control, not a substitute for restricting Docker access.

The service owner must explicitly accept this residual risk, identify the production host/environment covered by the decision, and record an approval date. If the risk is not accepted, replace Docker-discovery scheduling with a mechanism that does not grant a scheduler Docker API access (for example, host-level scheduling or an orchestrator-native CronJob) in a separately scoped change.

- **Risk owner:** ____________________
- **Environment/host:** ____________________
- **Decision:** Accept / Reject
- **Approval date:** ____________________
- **Review date:** ____________________
