# jarvis info

List all configured repositories from `repos.yaml`.

## Syntax

```bash
jarvis info
```

## Description

Displays all repositories configured in the `repos.yaml` file, including:
- Repository name
- GitHub URL
- Documentation directory
- Rendered documentation URL

## Example Output

```bash
$ jarvis info
Configured repositories:
============================================================
Name: HOPE
  URL: https://github.com/unicef/hope
  Docs dir: docs
  Rendered URL: https://hope.unicef.org/docs/
------------------------------------------------------------
Name: Country Report
  URL: https://github.com/unicef/country-report
  Docs dir: documentation
  Rendered URL: https://country-report.unicef.org/docs/
------------------------------------------------------------
Name: Aurora
  URL: https://github.com/unicef/aurora
  Docs dir: docs
  Rendered URL: https://aurora.unicef.org/docs/
------------------------------------------------------------
```

## Use Cases

- **Check configuration**: Verify which repositories are configured for ingestion
- **Debug**: Ensure repository names, URLs, and docs directories are correct
- **List available repos**: See which repo names can be used with `-r` option

## Notes

- This command reads from `CONFIG_PATH/repos.yaml`
- The `CONFIG_PATH` is set via environment variable
- Repository names shown here can be used with `-r` option in other commands
