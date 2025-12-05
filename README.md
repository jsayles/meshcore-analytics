# MAX - MeshCore Analytics eXchange

## Development

### Common Commands

```bash
# Run development server
uv run manage.py runserver

# Run tests
uv run manage.py test --parallel auto

# Check for outdated packages
uv pip list --outdated

# Load contacts from USB radio
uv run manage.py load_radio_data
```

### Package Management

```bash
# Add dependencies
uv add <package>
uv add --dev <package>

# Sync/install all dependencies from pyproject.toml
uv sync

# Update a specific package
uv add <package>@latest
```
