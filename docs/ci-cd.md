# CI/CD Overview

Workflows:
- ci/tests.yml: runs linting and pytest on feature/phase7 pushes and PRs
- ci/pr-checks.yml: quick lint checks for PRs
- ci/docker-build-and-publish.yml: builds service images and includes placeholders for registry login/push steps

Secrets:
- DOCKER_REGISTRY (placeholder)
- REGISTRY_USERNAME / REGISTRY_TOKEN

Notes:
- Registry credentials should be stored in GitHub Actions secrets.
- Terraform and k8s manifests are intentionally deferred to Phase 8.
