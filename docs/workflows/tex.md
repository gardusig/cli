# tex

`gardusig/tex` holds job-tailored LaTeX résumé sources. Workflow and Docker orchestration stay in `gardusig/cli`.

## Layout

- `lib/` — shared preamble, header, job bullets, education, awards, profile blurbs
- `versions/` — tailored entry points (`general.tex`, `backend-systems.tex`, …)

## Pipeline

| Config | Dockerfile |
| --- | --- |
| `pull-request/tex.yaml` | `docker/tex/tex.dockerfile` |

Stages: `lint` → `repo-hygiene` → `latex` → `pages_deploy`.

`versions/general.pdf` is copied to `resume.pdf` for GitHub Pages publish to **gardusig/gardusig** (`app_repo` on the pages job).

## Local dispatch

```bash
cli pipeline run pull-request tex --ref my-branch
```
