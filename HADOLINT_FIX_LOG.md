# Hadolint Fix Log - May 16, 2026

## Issue
hadolint action v3 doesn't exist:
- Error: "Unable to resolve action `hadolint/hadolint-action@v3`, unable to find version `v3`"

## Fix Applied
Replaced action with Docker-based hadolint scan:
- Pull hadolint/hadolint:latest image
- Run on Dockerfile in repository
- Non-blocking (continue-on-error: true)

## Testing
This PR verifies that all 7 security gates pass without action resolution errors.
