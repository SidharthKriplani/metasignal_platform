# MetaSignal Static Evidence Dashboard

## Purpose

The dashboard converts MetaSignal evidence artifacts into a visual public showcase.

It is static and local-first. It does not require a backend, hosted database, frontend framework, or paid infrastructure.

## Public Entry Point

The GitHub Pages entrypoint is:

    docs/index.html

## Local Entry Point

The local dashboard is generated at:

    outputs/dashboard/index.html

## Run

    PYTHONPATH=. python3 scripts/build_dashboard_v1.py
    PYTHONPATH=. python3 scripts/validate_dashboard_v1.py
    open outputs/dashboard/index.html

## Claim Boundary

The dashboard summarizes repo evidence. It does not convert MetaSignal into a production system. MetaSignal remains solo-built, non-production, and production-simulated.
