# TransitionCompassViz (leure-speed-to-zero)

A Quasar Project for interactive climate pathway visualization

## Configuration

The application uses a centralized configuration file `../model_config.json` to manage regional data settings:
This file is copied to frontend and backend via the root Makefile rule `make install-config`

```json
{
  "MODEL_PRIMARY_REGION": "Vaud",
  "AVAILABLE_REGIONS": ["Vaud", "Switzerland", "EU27"]
}
```

## Install the dependencies

```bash
yarn
# or
npm install
```

### Start the app in development mode (hot-code reloading, error reporting, etc.)

```bash
quasar dev
```

### Lint the files

```bash
yarn lint
# or
npm run lint
```

### Format the files

```bash
yarn format
# or
npm run format
```

### Build the app for production

```bash
quasar build
```

### Customize the configuration

See [Configuring quasar.config.js](https://v2.quasar.dev/quasar-cli-vite/quasar-config-js).

### Cross-platform

For cross-platform projects (arm64, amd64, Windows, Linux, macOS), it is generally not recommended to commit package-lock.json (or npm-shrinkwrap.json) for frontend projects that depend on native or optional dependencies, especially when using Docker and multi-architecture builds. This is because the lock file can cause platform-specific dependency resolution issues, as you have experienced.

Best practice for your scenario:

Do not commit package-lock.json or npm-shrinkwrap.json for the frontend if you want maximum compatibility across platforms and Docker builds.
Add package-lock.json and npm-shrinkwrap.json to your .gitignore for the frontend.
Let npm resolve dependencies at install time in the Docker build, ensuring the correct native modules are installed for the target platform.
However, for backend Node.js projects (not built in Docker, or not using native/optional deps), committing the lock file is usually recommended for reproducibility.

Summary for your frontend Docker build:

Do not commit package-lock.json or npm-shrinkwrap.json.
