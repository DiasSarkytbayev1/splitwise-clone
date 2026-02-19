# Dependency Management

This project manages Python dependencies using [pip-tools](https://github.com/jazzband/pip-tools) and `pip-sync`.

## Workflow

1. **Edit dependencies**
   Make changes to your dependencies in `api/requirements.in`.

2. **Compile requirements**
   Run:
   ```
   pip-compile api/requirements.in
   ```
   This generates/updates `api/requirements.txt` with pinned versions and hashes.

3. **Sync your environment**
   Run:
   ```
   pip-sync api/requirements.txt
   ```
   This will install/uninstall packages to match exactly what is specified in `api/requirements.txt`.

## Notes

- **Hashes**: The `--hash` lines in `requirements.txt` ensure integrity and security by verifying downloaded packages.
- **Do not edit `requirements.txt` manually**. Always update dependencies via `requirements.in` and recompile.
- **pip-sync**: Only packages listed in `requirements.txt` will be installed; others will be removed.
