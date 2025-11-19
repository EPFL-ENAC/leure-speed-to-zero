# Adding a New Sector

## Quick Overview

A sector = navigation item with charts/KPIs organized in subtabs + associated levers

## Steps

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

## Key Points

- **Output IDs**: Must match backend model outputs exactly
- **Chart types**: Available types (just change the `"type"` field):
  - `StackedArea` - Stacked area chart (shows composition over time)
  - `Line` - Line chart (shows trends over time)
  - `Bar` - Bar chart (compares values across categories)
  - `StackedBar` - Stacked bar chart (shows composition across categories)
  - `Sankey` - Sankey diagram (shows flow relationships, requires special data format)
- **Translations**: Required for all titles (enUS, frFR, deDE)
- **Levers**: Define in `/frontend/src/config/levers.ts` if new
- **Plot labels**: Add output labels in `/frontend/src/config/plotLabels.ts`

## Example: See Forestry

- Config: `/frontend/src/config/subtabs/forestry.json`
- Component: `/frontend/src/pages/sectors/ForestryTab.vue`
- Entry in `sectors.ts` and `routes.ts`
