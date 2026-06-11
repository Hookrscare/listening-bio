# GitHub Publishing

Publishing is currently blocked by local tooling, not by the project code.

Current checks from `scripts/check_python.py`:

- Python works inside `.venv`
- `git` exists at `/usr/bin/git`, but macOS blocks it until the Xcode license is accepted
- `gh` is not installed
- Docker is not installed

To publish this project to GitHub from this machine:

```bash
sudo xcodebuild -license
brew install gh
gh auth login
git init
git add .
git commit -m "Build AI biodiversity backend foundation"
gh repo create ai-biodiversity-backend --private --source=. --remote=origin --push
```

Use `--public` instead of `--private` if the repo should be public.

After publishing, continue with the next backend refinement pass:

- Add real Postgres integration tests once Docker is available.
- Add API endpoints for raw model outputs and reports.
- Add a background worker abstraction for replacing mock processing with BirdNET/YAMNet adapters.
- Add authentication before any multi-user deployment.

