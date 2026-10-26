---
title: Updating the documentation website
editLink: false
---

# Updating the documentation website

The documentation repository gathers project pages and builds the VitePress website. A product release can request a refresh; changes to the site's main branch and manual requests start the same deployment.

```mermaid
%%{init: {"htmlLabels": false}}%%
flowchart TB
    PUSH["Documentation push to<br/>main"] --> SSH["GitHub runner connects<br/>to documentation server<br/>over SSH"]
    RELEASE["Product sends<br/>docs-release event"] --> SSH
    MANUAL["Manual deployment<br/>request"] --> SSH
    SSH --> REFRESH["Server refreshes<br/>documentation main; runs<br/>deploy.sh"]
    REFRESH --> REVISIONS["Select latest release tags<br/>for all submodules<br/>including .github"]
    REVISIONS --> BUILD["Docker Compose builds<br/>site image"]
    BUILD --> OK{"Build succeeded?"}
    OK -->|Yes| SERVE["Start updated container"]
    OK -->|No| FAIL["Job fails; previous<br/>container continues<br/>serving"]
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class PUSH,RELEASE,MANUAL event
    class SSH,REFRESH,REVISIONS,BUILD,SERVE work
    class OK check
    class FAIL failure
```

## Which documentation is published

Git submodules record a specific commit from another repository. Deployment fetches product submodules and selects the latest `v*` tag using Git's version sorting. A product without a matching tag stays at its existing revision.

The central .github repository publishes versioned release tags through its release workflow and sends the docs-release dispatch to the documentation repository, triggering server-side tag checkout and container rebuild just like product repositories.

## Server handoff and failure evidence

The GitHub runner performs the SSH handoff. The server has repository access and performs checkout, submodule selection and container build. The workflow serialises requests with `cancel-in-progress: false`.

If the site remains old, inspect the product notification, documentation deployment log, selected tags and central submodule pointer. The notification identifies a product and tag, but deploy.sh applies its own revision-selection policy.

Server credentials and operations stay with the documentation repository. See [publishing documentation](/getting-started/publishing-docs), [deploy workflow](https://github.com/ARTTU-Software/documentation/blob/main/.github/workflows/deploy.yml) and [deploy.sh](https://github.com/ARTTU-Software/documentation/blob/main/deploy.sh).

[Back to CI/CD overview](/architecture/github)
