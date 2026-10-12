# 0002. Stateless service: no database, no accounts, no tenancy

Status: accepted

## Context
The playbook's layers on databases, auth, permissions, tenancy, payments and webhooks assume a multi-user
SaaS. This product is an anonymous form in front of a model. Nothing needs to be remembered between
requests.

## Decision
Do not add a database, authentication, roles, organisations, payments or webhooks. Every request is
independent. No `organization_id`, no permission matrix.

## Alternatives considered
- Add accounts and history "for later": invents requirements nobody agreed to, adds a data-protection
  burden (stored health-adjacent inputs) and a large attack surface.
- Add API keys to protect the endpoint: no user to issue them to; rate limiting is the proportionate
  control for now.

## Consequences
- Nothing to back up, migrate, delete on request, or leak from storage.
- Anyone on the internet can call the API, so rate limiting and strict validation carry the load.
- Per-user quotas, history and personalisation are impossible until this decision is revisited.
- Revisit if: predictions need to be stored, the endpoint becomes costly to run, or abuse appears.
  A new system-design pass (and an `organization_id`-style tenancy decision) must come first.
