# Install

Install the published CLI package from PyPI:

```bash
pip install gardusig-cli
cli --version
```

The distribution is `gardusig-cli`; the executable is `cli`.

After installation, configure credentials and paths:

```bash
cli configure list
cli configure set gh.token --stdin
cli configure import-env
```

Pipelines use the same install path through `pip install --no-cache-dir gardusig-cli`.
