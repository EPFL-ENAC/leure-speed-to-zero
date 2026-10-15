# Adding a New Lever

## Quick Overview

A lever = user control that adjusts model parameters, displayed in sector sidebar.

The list of levers comes from the model (`config/lever_position.json` in the
model package). The app only needs the texts, in one JSON file per profile:

- `/frontend/src/config/levers/default.json`: levers of transition-compass-model
- `/frontend/src/config/levers/tcaf.json`: levers of tcaf-model

Edit only the file of your model. A profile with no file of its own uses
`default.json`.

## Steps

### 1. Add Lever Texts

Add to the JSON file of your profile:

```json
{
  "code": "lever_{your-lever-id}",
  "title": {
    "enUS": "English Title",
    "frFR": "Titre français",
    "deDE": "Deutscher Titel"
  },
  "group": {
    "enUS": "Group Name",
    "frFR": "Nom du groupe",
    "deDE": "Gruppenname"
  },
  "headline": {
    "enUS": "Section Headline",
    "frFR": "Titre de section",
    "deDE": "Abschnittstitel"
  },
  "range": [1, 2, 3, 4],
  "type": "num",
  "difficultyColors": [
    { "min": 1, "max": 1, "color": "#CFE3F7", "label": "lever.difficulty.easy" },
    { "min": 2, "max": 2, "color": "#92BFEB", "label": "lever.difficulty.moderate" },
    { "min": 3, "max": 3, "color": "#559ADE", "label": "lever.difficulty.hard" },
    { "min": 4, "max": 4, "color": "#1876D2", "label": "lever.difficulty.ambitious" }
  ],
  "popupText": {
    "enUS": "Explanation text",
    "frFR": "Texte explicatif",
    "deDE": "Erklärungstext"
  }
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

- **Code**: Must match the lever key in the model `lever_position.json`
- **Type**: `"num"` for numeric, `"char"` when `range` lists named options (the value is the position in the list)
- **Range**: Levels of the slider. The model has levels 1 to 4
- **Group**: Organizes levers in sidebar sections
- **Headline**: Higher-level grouping above groups
- **Difficulty colors**: Visual feedback for ambition levels
- **Popup text**: Optional detailed explanation for users when opened in popup

## Forgot a lever?

- The app does not break: a lever with no texts is sent to the model at its
  default level from `lever_position.json`, it just has no slider.
- The backend tests (`cd backend && make test`, also run in CI) fail and name
  the missing lever. So the PR that bumps the model shows it.

## Example

See `lever_harvest-rate` in `/frontend/src/config/levers/default.json`
