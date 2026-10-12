# 0001. One FastAPI service plus a separately hosted static frontend

Status: accepted

## Context
A single model has to be served to a browser form. Team size is one. The playbook recommends a modular
monolith for almost every early product.

## Decision
One FastAPI process for all server-side work, organised in layers (routes, services, domain). The React
app is built to static files and hosted separately, calling the API over HTTPS.

## Alternatives considered
- FastAPI serving the built frontend itself: one deploy instead of two, but mixes caching and security
  header needs of static files and the API, and couples release cycles.
- Streamlit or Gradio: fastest, but the owner chose React + FastAPI.
- Microservices: no reason at this size.

## Consequences
- Two deploy targets, so CORS must be configured explicitly (`CORS_ORIGINS`).
- Security headers for the SPA (CSP, framing) must be set at the static host. The API sets its own.
- The frontend can be redeployed without touching the model, and the reverse.
