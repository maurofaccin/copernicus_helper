
# Copernicus Helper

This is a CLI Copernicus helper to make the life easier.

## Envs

Instead of the local `~/.cdsapirc` polluting your home folder, one can use environment variables:

- `CDSAPI_URL` to set the `url`
- `CDSAPI_KEY` to set the personal `key`
- `CDSAPI_RC` to set a curstom location for the configuration file

Setting `url` and `key` by env vars overwrite everything.
Setting the config file by env var is the second choice
Looking at `~/.cdsapirc` is the fallback option.
