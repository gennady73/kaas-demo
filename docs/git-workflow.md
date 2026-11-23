# What to synchronize with Git

Revision 0.1, 2026-11-23. Based on inspection of the actual local repositories and remotes; no push was performed while writing this guide.

## Repository boundaries

| Local directory | Git remote / purpose | What belongs here |
| --- | --- | --- |
| `/home/gunger/Projects/kaas-solution/kaas-demo` | `https://github.com/gennady73/kaas-demo.git` | GitOps manifests, environment overlays, bootstrap definitions, portable guides, small synthetic test inputs and sanitized result summaries |
| `/home/gunger/Projects/kaas-solution/kafka-load-test` | `https://github.com/gennady73/kafka-load-test.git` | Test-generator source, extension/build integration and its tests; local `preflight/` work is currently untracked and must be reviewed in this repository separately |
| `/home/gunger/Projects/kaas-solution` itself | Not a Git repository | Shared SRS, project context, validation register, local environment evidence and coordinator tools; these files are not backed up by pushing either child repository |

Do not run `git init` or `git add .` in the parent merely to publish the demo. That would require a separate decision about the parent repository, private evidence, source documents and nested repositories. If architecture documents need version control, choose a separate private architecture repository or deliberately promote reviewed portable documents into `kaas-demo/docs/`; do not bulk-copy the workspace.

The `kaas-demo` repository is public. Commit no access tokens, kubeconfigs, passwords, private keys, Secret manifests with credentials, raw customer records or unreviewed cluster exports. Its `.gitignore` is a convenience, not a security check: inspect staged contents. Large generated outputs and logs belong in an evidence store, with sanitized summaries and references in Git.

## Local files to GitHub

Run commands in the relevant child repository. For the current guide/result changes:

```sh
cd /home/gunger/Projects/kaas-solution/kaas-demo
git status --short --branch
git remote -v
git fetch origin
git diff
git diff --cached
```

Review any existing local changes first. The previously prepared implementation history is preserved on `local-prepublication-20261122`; keep it. Normal work uses `main` tracking `origin/main`. Because the first publication used GitHub's browser uploader, remote commit IDs differ from the original local commits even though their trees matched exactly. Do not force-push the historical branch over `main`.

For the current documentation update, create a branch and stage only these reviewed files:

```sh
git switch -c docs/bootstrap-and-git-guides
git add README.md docs/bootstrap-guide.md docs/git-workflow.md docs/deployment-sequence.md docs/implementation-status.md docs/operator-stage-result-2026-11-22.md
git diff --cached --check
git diff --cached
git commit -m "Document Kafka operator bootstrap and Git workflow"
git push -u origin docs/bootstrap-and-git-guides
```

Choose another branch name if that name already exists. Open a pull request into `main` and merge after review. If `origin/main` advanced, integrate it into your working branch and resolve conflicts before merging; do not overwrite remote changes. To update a clean local `main` after the PR merges:

```sh
git switch main
git pull --ff-only origin main
```

If the working tree is not clean or histories diverge, inspect and resolve that condition before pulling. These commands are guidance; no branch, commit or push was made for this documentation request.

## GitHub browser login versus Git credentials

Signing into GitHub in the browser did not configure this machine's command-line Git credential helper. The first project publication therefore used the signed-in browser. A successful anonymous `git fetch` from this public repository does not establish push access.

Configure an approved Git Credential Manager or GitHub CLI authentication on the machine where `git push` runs. If GitHub CLI is installed, its documented flow is:

```sh
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git --hostname github.com
```

Complete the authorization yourself, then use the normal push command. Do not place a token in a remote URL, this guide or chat. See [GitHub's credential guidance](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git) and [GitHub CLI setup-git](https://cli.github.com/manual/gh_auth_setup-git), checked 2026-11-23. This guide does not install GitHub CLI or configure credentials automatically.

## GitHub to OpenShift is a separate operation

`git push` publishes source. ArgoCD synchronization applies selected source to the cluster. OLM InstallPlan approval installs or updates an operator. These are three separate steps.

The existing Application `openshift-gitops/kaas-demo-operator` is pinned to `7542a93c5aee9aad281c62ba074e1de7db7b7624`, path `environments/dev/operator`, with manual sync. New commits on `main`, including documentation commits, do not move this pin or trigger automatic synchronization. Promote a reviewed deployment revision explicitly through the bootstrap/Application configuration workflow and verify the actual revision before an authorized manual sync. Do not use a blanket sync of all applications.

Its AppProject currently permits only OperatorGroup and Subscription resources in the intended namespaces. Kafka cluster/topic resources require a separately reviewed application/scope update. Updating Git does not authorize a newer Kafka operator InstallPlan. See the [bootstrap guide](bootstrap-guide.md) for that workflow.

For air-gapped targets, promote reviewed source revisions to the accessible internal Git mirror and required images to the internal registry. Public GitHub reachability in the sandbox is not disconnected-installation evidence.
