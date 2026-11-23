# Access control required before Operator exposure

The current RADP 0.5.1 candidate API routes do not implement application-level
authentication or authorization. The landing page and report endpoints added in
this release must therefore not be interpreted as an authenticated user portal.

Before exposing the application to Operators or to a network segment beyond the
currently approved administrative boundary, decide and document:

1. The offline identity authority (for example, an already approved directory or
   identity provider available inside the Transport environment).
2. User and administrator roles, including which users may preview or download
   certificate data.
3. Session/token lifecycle, logout, credential recovery, and account revocation.
4. Protection against CSRF where cookie-based sessions are used, and appropriate
   CORS and security-header policy.
5. Audit events for authentication, authorization failures, and report downloads.
6. Reverse-proxy/TLS termination and trusted network boundaries in the offline
   environment.

Do not substitute a hard-coded password, shared application password, or an
unreviewed custom login form for this decision. Until the identity and access
model is implemented and tested, restrict access at the network and host layers
according to the deployment security policy.

This is a release gate for broader Operator exposure, not a claim that network
restriction alone is equivalent to application authentication.
