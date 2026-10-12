# HashScrap URL and destination security policy

## What the application policy enforces

The URL policy fails closed unless all of these checks pass:

- Scheme is HTTP or HTTPS.
- A hostname exists and URL userinfo is absent.
- The destination port is on the explicit allowlist (80 and 443 by default).
- Local-only hostnames are rejected.
- Literal IPs and every resolved address are globally routable; loopback, private,
  link-local, multicast, unspecified, reserved, and known cloud metadata addresses are rejected.
- Empty DNS answers, resolver errors, and mixed public/private DNS answers are rejected.
- Redirect targets must be resolved relative to the current URL and validated again.
- URL fragments are removed from the normalized request URL.

The resolver is injectable for deterministic tests. Tests must never need the public Internet.

## Important integration limitation

A validation result is **not sufficient on its own** to prevent DNS rebinding. The future downloader must enforce destination validation as close as possible to connection establishment and must not perform an unchecked second DNS lookup after validation. It must revalidate each redirect before following it. If the HTTP client cannot pin or otherwise enforce the validated destination, that limitation must be documented and the deployment egress controls must remain the hard boundary.

Do not treat this module as a substitute for network isolation.

## Recommended deployment egress policy

Run collection workers on a dedicated Docker network with only the outbound access they require. At the host/firewall or egress-proxy layer:

- Deny access to loopback, private, link-local, multicast, reserved, and internal service ranges.
- Explicitly block cloud metadata endpoints, including 169.254.169.254.
- Do not allow workers to reach PostgreSQL, Docker control sockets, host administration ports, or other internal services except through narrowly defined application interfaces.
- Permit only required outbound protocols and ports.
- Keep PostgreSQL on a private Compose network and do not publish its port to the Internet.
- Log policy decisions and rejection reasons without logging credentials or sensitive query parameters.

## Scope and non-goals

This policy is a guardrail for collection of public or otherwise authorized sources. It does not bypass authentication, paywalls, CAPTCHAs, access controls, or source rate limits. A future Scrapy downloader integration must invoke this policy before every request and redirect and add integration tests for the actual request path.
