# Adding a New Sector

## Quick Overview

A sector = navigation item with charts/KPIs organized in subtabs + associated levers + backend model integration

## Steps

### 0. Backend Configuration

Add sector to `/backend/model_config.json` with its dependencies:

```json
{
  "SECTORS_TO_RUN": {
    "your-sector": ["climate", "lifestyles", "your-sector"]
  }
}
```

**Important**: List sectors in execution order, including all dependencies. The order matters and should match the sequence in `/backend/model/interactions.py`.

### 1. Create Subtabs Config

Create `/frontend/src/config/subtabs/{sector-name}.json`:

```json
{
  "kpis": [],
  "subtabs": [
    {
      "title": { "enUS": "Title", "frFR": "Titre", "deDE": "Titel" },
      "charts": ["ChartId1", "ChartId2"],
      "route": "route-name"
    }
  ],
  "charts": {
    "ChartId1": {
      "title": { "enUS": "Chart Title", "frFR": "...", "deDE": "..." },
      "type": "StackedArea", // or "Line"
      "unit": "kWh",
      "outputs": ["output-id-1", "output-id-2"]
    }
  }
}
```

### 2. Create Vue Component

Create `/frontend/src/pages/sectors/{SectorName}Tab.vue`:

```vue
<template>
  <SectorTab sector-name="{sector-name}" sector-display-name="{sector-name}" :config="{sectorName}Config" />
</template>

<script setup lang="ts">
import {sectorName}Config from 'config/subtabs/{sector-name}.json';
import SectorTab from 'components/SectorTab.vue';
</script>
```

### 3. Register in Config

Add to `/frontend/src/config/sectors.ts`:

```ts
{
  label: { enUS: 'Name', frFR: 'Nom', deDE: 'Name' },
  value: '{sector-name}',
  icon: 'icon_name',  // Material Icons
  levers: ['lever_id1', 'lever_id2'],
}
```

### 4. Add Route

Add to `/frontend/src/router/routes.ts`:

```ts
{
  path: '{sector-name}/:subtab?',
  name: '{sector-name}',
  component: () => import('src/pages/sectors/{SectorName}Tab.vue'),
}
```

### 5. Backend Model Module

Create your sector module in `/backend/model/{sector_name}_module.py` and integrate it in `/backend/model/interactions.py`:

```python
from model.your_sector_module import your_sector

# In runner function, add after dependencies:
if 'your-sector' in sectors:
    start_time = time.time()
    TPE['your-sector'], KPI['your-sector'] = your_sector(
        lever_setting, years_setting, DM_input['your-sector'], interface
    )
    logger.info('Execution time Your-Sector: {0:.3g} s'.format(time.time() - start_time))
```

## Key Points

### Backend

- **Sector Dependencies**: Define in `model_config.json` - list all sectors your sector depends on
- **Execution Order**: Must match the order in `interactions.py` (e.g., climate → lifestyles → transport → buildings)
- **Data Loading**: Add sector to datamatrix loading if it requires pre-processed data
- **Performance**: Only sectors listed in dependencies will run when this sector is requested

### Frontend

- **Output IDs**: Must match backend model outputs exactly
- **Automatic Optimization**: SectorTab component automatically sets current sector for optimized API calls
- **Chart types**: Available types (just change the `"type"` field):
  - `StackedArea` - Stacked area chart (shows composition over time)
  - `Line` - Line chart (shows trends over time)
  - `Bar` - Bar chart (compares values across categories)
  - `StackedBar` - Stacked bar chart (shows composition across categories)
  - `Sankey` - Sankey diagram (shows flow relationships, requires special data format)
- **Translations**: Required for all titles (enUS, frFR, deDE)
- **Levers**: Define in `/frontend/src/config/levers.ts` if new
- **Plot labels**: Add output labels in `/frontend/src/config/plotLabels.ts`

## Debugging

- **Check sector config**: `GET /api/debug-sectors`
- **Reload config**: `POST /api/reload-config`
- **Test specific sector**: `GET /api/v1/run-model?sector=your-sector`

## Example: See Forestry

- Backend Config: `/backend/model_config.json` (SECTORS_TO_RUN)
- Backend Module: `/backend/model/forestry_module.py`
- Frontend Config: `/frontend/src/config/subtabs/forestry.json`
- Frontend Component: `/frontend/src/pages/sectors/ForestryTab.vue`
- Entry in `sectors.ts` and `routes.ts`
