# RA Data Service Explorer

`ra-ds-explorer` is an enterprise-oriented Python client and service framework for interacting with GOST-enabled Registration Authority (RA) REST APIs.

The project provides:

- authenticated RA API communication
- CryptoPro-compatible mutual TLS transport
- typed API models
- certificate/user/request operations
- offline fixture-based development mode
- reporting and export capabilities
- service-layer abstractions suitable for GUI integration

The project is designed for secured enterprise environments where:

- client authentication uses certificates
- CryptoPro CSP tooling is already deployed
- direct OpenSSL integration is undesirable
- internet access may be restricted
- runtime environments must be controlled and reproducible

---

# Current Project Status

The current implementation provides:

## API Client Layer

Implemented:

- certificate API access
- user API access
- certificate request API access
- pagination handling
- response validation
- typed schema parsing

Architecture:

```

Application Services
↓
API Client
↓
Transport Layer
↓
RA REST API

```

---

# Transport Architecture

The project intentionally separates API logic from transport execution.

Supported transports:

## Fixture Transport

Used for:

- offline development
- deterministic testing
- CI pipelines
- API contract validation

Flow:

```

Application
↓
API Client
↓
Fixture Transport
↓
Local JSON Fixtures

```

---

## CryptoPro Curl Transport

Used for enterprise environments.

Flow:

```

Application
↓
API Client
↓
CryptoPro Curl Wrapper
↓
CryptoPro CSP
↓
GOST Mutual TLS
↓
RA API

```

The project does not implement custom cryptography.

It relies on:

- vendor-supported CryptoPro tooling
- enterprise PKI configuration
- certificate containers managed externally

---

# Project Architecture

Current structure:

```

rads_explorer/

├── api/
│   ├── client.py
│   ├── endpoints.py
│   ├── schemas/
│   └── parsers.py
│
├── application/
│   ├── certificate_service.py
│   ├── user_service.py
│   ├── cert_request_service.py
│   └── reports
│
├── infrastructure/
│   ├── transport/
│   └── fixtures/
│
├── data/
│   ├── repository.py
│   ├── reports.py
│   └── export/
│
├── interfaces/
│   └── FastAPI interface layer
│
└── container/
└── dependency composition

```

---

# Development Mode

The project supports fully offline execution.

Fixtures provide:

- certificates
- users
- certificate requests
- certificate details

Example workflow:

```

Fixture JSON
↓
Fixture Loader
↓
Repository
↓
Reports / Services / API

```

This allows development without:

- RA server access
- CryptoPro installation
- network connectivity

---

# Testing

The project contains:

## Unit Tests

Covers:

- services
- parsers
- data layer
- exports

## API Contract Tests

Covers:

- fixture API behavior
- schema validation
- certificate parsing

## Integration Tests

Prepared for:

- real RA API access
- CryptoPro transport verification

---

# Reporting and Export

Implemented:

## Certificate Reports

Examples:

- expiring certificates
- issuer distribution
- certificate searches

## Export

Supported:

- XLSX generation

Example:

```

RA API
↓
Repository
↓
Report Service
↓
XLSX Export

```

---

# Running Locally

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
pytest
```

Run demo:

```bash
python tools/run_demo.py
```

Run fixture API:

```bash
uvicorn rads_explorer.interfaces.main:app
```

---

# Configuration

Runtime configuration uses environment variables.

Example:

```env
RADS_TRANSPORT=curl

RADS_API_BASE_URL=https://service-host

RADS_CURL_PATH=/opt/product/bin/amd64/curl

RADS_CERT_THUMBPRINT=<certificate-thumbprint>
```

Transport selection:

```env
RADS_TRANSPORT=curl
```

or:

```env
RADS_TRANSPORT=curl
```

---

# Deployment Model

Target environments are expected to use isolated runtimes.

Recommended:

```
/opt/ra-ds-explorer/

├── python/
├── venv/
├── app/
├── wheels/
├── logs/
└── exports/
```

Goals:

* no modification of system Python
* reproducible installation
* offline package installation
* controlled enterprise deployment

---

# Security Model

The project follows these principles:

* no private key handling inside Python
* no custom cryptographic implementation
* no OpenSSL engine integration
* no bypassing enterprise PKI controls

Authentication remains the responsibility of:

* CryptoPro CSP
* enterprise certificate infrastructure
* configured certificate stores

---

# Planned Transition

The original long-term vision of the project includes evolving into a full operator-facing application.

Planned transition:

```
PySide6 GUI
      ↓
Application Services
      ↓
RA Client Framework
      ↓
CryptoPro Transport
      ↓
RA API
```

Future capabilities may include:

* desktop GUI
* certificate lifecycle dashboards
* operator workflows
* interactive search
* certificate inspection
* report generation interface
* enterprise workstation deployment

The current architecture intentionally preserves this path.

The GUI layer is not implemented yet because the service and transport foundations are being stabilized first.

---

# Non-Goals

The project does not aim to:

* replace CryptoPro CSP
* implement GOST cryptography itself
* bypass enterprise PKI policies
* replace RA server functionality
* depend on cloud services
* require internet connectivity during operation

---

# License

See: [LICENSE](LICENSE.md)
