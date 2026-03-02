# AU199.github.io

## Statbotics + static GitHub Pages workflow

This repository keeps the scouting page fully static for GitHub Pages.

- `main.py` fetches data from the Statbotics REST API and writes a local `scouting-data.json` file.
- `scouting.html` reads `scouting-data.json` in the browser and renders team, season, and match information.

### Generate scouting data

```bash
python3 main.py --team 199 --year 2024
```

If every API call succeeds, `scouting-data.json` will contain the latest data bundle.
If some endpoints fail, the script still writes the file and stores error messages under `errors`.
