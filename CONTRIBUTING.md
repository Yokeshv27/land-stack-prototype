# Contributing

## Local setup

Create a virtual environment, install `requirements.txt`, run `python -m ai.training`, and seed with `python -m database.seed`. Run `pytest` before opening a pull request.

## Data and security rules

- Never commit real land records, personal data, databases, credentials, or `uploads/`.
- Use only fictional sample documents in `sample_data/`.
- Do not claim that a Prototype ULPIN, map polygon, or 3D building is official government, cadastral, or LiDAR data.
- Keep authorization checks in the service/API layer; hiding a button is not security.

## Pull requests

Describe the user-facing change, list tests run, and include a screenshot for Streamlit UI changes. Keep modules small and add tests for new security or data-handling behaviour.
