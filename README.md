# Monorepo for Referendum ATP and Data Service

This repository contains two primary services for the application:

1. **Go Service**: Implements the **Authenticated Transfer Protocol (ATP)** for user events and data repositories.
2. **Python Service**: Provides the **data layer**, handling database interactions and data processing for the application.

## Directory Structure

- `user_service/`: Contains the Go implementation of the Authenticated Transfer Protocol. See the [README](./user_service/README.md) in this directory for more details.
- `data_service/`: Contains the Python implementation of the data layer. See the [README](./data_service/README.md) in this directory for more details.

Each service includes its own documentation, dependencies, and setup instructions.

## Prerequisites

### Go

1. Download and install Go from the [official Go website](https://go.dev/dl/).
2. Follow the instructions for your operating system to complete the installation.
3. Verify the installation:
   ```bash
   go version
   ```
4. Install project dependencies:
   ```bash
   cd ./user_service && go mod tidy
   ```
5. Install [golangci-lint](https://golangci-lint.run/welcome/install/#local-installation)

### Python and UV

1. Download and install Python

   - **Linux (Using `pyenv`)**:

   ```bash
   sudo apt update
   sudo apt install -y build-essential zlib1g-dev libssl-dev libncurses5-dev libnss3-dev libreadline-dev libffi-dev curl
   curl https://pyenv.run | bash
   pyenv install 3.13.3
   pyenv global 3.13.3
   ```

   - **macOS (Using `brew`)**:

   ```bash
   brew install python@3.13
   ```

   - **Windows**:

   Download the installer from the [official Python website](https://www.python.org/downloads/release/python-3114/).

2. Install UV

```bash
python -m pip install --upgrade pip
python -m pip install uv
```

3. Install project dependencies:

```bash
uv pip install --all-extras --requirements ./data_service/pyproject.toml
```

## Code Quality

```bash
# Install and configure pre-commit hooks
pip install pre-commit
pre-commit install

# Manual code formatting
gofmt -w ./user_service
black ./data_service
# Generate API documentation
make docs
```

## Monitoring

- CloudWatch for logging
- UptimeRobot monitoring for Prod and Dev APIs

## 📝 Version Management

- Version format: MAJOR.MINOR.PATCH
- Automatic versioning via commit messages:
  - `#major`: Breaking changes (e.g., API changes, schema updates)
  - `#minor`: New features (backward compatible)
  - Default: Patch updates (bug fixes, minor improvements)
- Release tags are automatically created
- Changelog is generated from commit history

## 🤝 Contributing

1. **Branch Naming**

   - `<author>/<description>`

2. **Development Process**
   - Create branch from `main`
   - Develop and test locally
   - Ensure all tests pass
   - Update documentation if needed
   - Submit PR for review

---

For further details, navigate to the respective subdirectory and refer to the README file.
