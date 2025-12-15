# Adding a Region Flag

## Quick Steps

1. **Get a rectangular SVG** for your region (use [SVGOMG](https://jakearchibald.github.io/svgomg/) to optimize)
2. **Name it lowercase**: `eu27.svg` for region "EU27"
3. **Copy to**: `frontend/src/assets/flags/eu27.svg`
4. **Verify** region exists in `backend/model_config.json`:
   ```json
   "AVAILABLE_REGIONS": ["Vaud", "Switzerland", "EU27"]
   ```
5. **Test**: `make run` and switch regions

## Examples

| Region      | Filename          |
| ----------- | ----------------- |
| Vaud        | `vaud.svg`        |
| Switzerland | `switzerland.svg` |
| EU27        | `eu27.svg`        |

## Troubleshooting

**Flag not showing?**

- Check filename is lowercase and matches region name
- Verify SVG is valid (open in browser)
- Clear cache: `Ctrl+Shift+R`

**Wrong flag?** Filename must exactly match region name (lowercase)

**Distorted?** Use rectangular SVG with 3:2 ratio (`viewBox="0 0 900 600"`)

## Resources

Free flags: [Wikimedia Commons](https://commons.wikimedia.org/wiki/Flags) | [Flagpedia](https://flagpedia.net/) | [Flag Icons](https://github.com/lipis/flag-icons)
