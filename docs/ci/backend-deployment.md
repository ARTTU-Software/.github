---
title: Deploying the backend
editLink: false
---

# Deploying the backend

The Backend repository has its own deployment procedure. A push to its main branch asks the production server to run the server's redeployment script.

```mermaid
flowchart TB
    PUSH["Push reaches Backend main"] --> RUNNER["GitHub starts Ubuntu runner"]
    RUNNER --> SSH["Connect to production server with configured SSH credentials"]
    SSH --> SCRIPT["Change to /srv/docker/compose; run bash redeploy.sh"]
    SCRIPT --> RESULT{"Remote command succeeded?"}
    RESULT -->|Yes| PASS["Deployment job completes successfully"]
    RESULT -->|No| FAIL["Job fails; inspect SSH and server script output"]
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class PUSH event
    class RUNNER,SSH,SCRIPT,PASS work
    class RESULT check
    class FAIL failure
```

## What the workflow tells us

The checked-in workflow defines the connection and command. The server's `redeploy.sh` controls the actual update. Health checks, rollback and database migration behaviour therefore need to be documented with the server procedure.

This deployment starts on a push to main. Publishing a release is a separate operation.

## Configuration and investigation

The workflow reads `PROD_HOST`, `PROD_USER` and `PROD_PASSWORD` from repository secrets and uses `appleboy/ssh-action`. For connection failures, inspect the SSH step and runner-to-server access. If the script starts and fails, use its output and the server's deployment records.

Source: [Backend deployment workflow](https://github.com/ARTTU-Software/Backend/blob/main/.github/workflows/deploy.yml). Keep server commands and credential changes in that repository.

[Back to CI/CD overview](/architecture/github)
