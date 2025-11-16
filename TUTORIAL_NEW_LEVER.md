# Adding a New Lever

## Quick Overview

A lever = user control that adjusts model parameters, displayed in sector sidebar

## Steps

### 1. Add Lever Definition

Add to `/frontend/src/config/levers.ts`:

```ts
{
  code: 'lever_{your-lever-id}',
  title: {
    enUS: 'English Title',
    frFR: 'Titre français',
    deDE: 'Deutscher Titel',
  },
  group: {
    enUS: 'Group Name',
    frFR: 'Nom du groupe',
    deDE: 'Gruppenname',
  },
  headline: {
    enUS: 'Section Headline',
    frFR: 'Titre de section',
    deDE: 'Abschnittstitel',
  },
  range: [1, 2, 3, 4],  // Adjust min/max as needed
  type: 'num',
  difficultyColors: [
    { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
    { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
    { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
    { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
  ],
  popupText: {  // Optional: shown in lever details popup
    enUS: 'Explanation text',
    frFR: 'Texte explicatif',
    deDE: 'Erklärungstext',
  },
}
```

### 2. Associate with Sector

Add lever code to sector in `/frontend/src/config/sectors.ts`:

```ts
{
  value: 'your-sector',
  // ...
  levers: [
    'lever_{your-lever-id}',
    // ... other levers
  ],
}
```

## Key Points

- **Code**: Must be unique and match backend lever ID
- **Type**: `'num'` for numeric, other types available
- **Range**: `[min, max]` - defines slider bounds
- **Group**: Organizes levers in sidebar sections
- **Headline**: Higher-level grouping above groups
- **Difficulty colors**: Visual feedback for ambition levels

## Example

See `lever_harvest-rate` in `/frontend/src/config/levers.ts` (line ~2107)
