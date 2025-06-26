# leure-speed-to-zero

The tool will integrate PyCalc models for real-time computations, provide interactive data visualizations, and support multilingual accessibility. It will be designed for scalability and maintainability with version control, CI/CD, and thorough documentation. Stakeholder engagement will guide its development through workshops and iterative improvements.

**Access the platform here:**

**dev url: [https://speed-to-zero-dev.epfl.ch/](https://speed-to-zero-dev.epfl.ch/)**  
**prod url: [https://speed-to-zero.epfl.ch/](https://speed-to-zero.epfl.ch/)**

## Contributors

- EPFL - (Research & Data): Dr. Gino Baudry (EPFL, gino.baudry[at]epfl.ch), Dr. Paola Paruta (EPFL, paola.paruta[at]epfl.ch), Dr. Edoardo Chiarotti (E4S, edoardo.chiarotti[at]epfl.ch), Agathe Crosnier (EPFL, agathe.crosnier[at]epfl.ch).
- EPFL - ENAC-IT4R (Implementation): Pierre Ripoll, Pierre Guilbert
- EPFL - ENAC-IT4R (Project Management): Pierre Ripoll
- EPFL - ENAC-IT4R (Contributors): --

## Development

### Prerequisites

- Node.js (v22+)
- npm
- Python 3.12 (uv is better)
- Docker

### Linux/Mac Setup (Recommended)

For Linux and Mac users, you can use the provided Makefile for easy setup and development:

#### Installation

```bash
# Clone the repository
git clone https://github.com/EPFL-ENAC/leure-speed-to-zero.git
cd leure-speed-to-zero

# Install all dependencies (backend + frontend) and set up git hooks
make install
```

#### Running the Development Environment

```bash
# Run both backend and frontend servers
make run
```

This will start:

- Backend at http://localhost:8000 (API docs at http://localhost:8000/docs)
- Frontend at http://localhost:9000

#### Other Useful Commands

```bash
make clean        # Clean node_modules and package-lock.json
make uninstall    # Remove git hooks and clean dependencies
make lint         # Run linter checks
make format       # Format code with prettier
make run-backend  # Run backend only
make run-frontend # Run frontend only
```

### Windows Setup

If you're on Windows without WSL2, you can set up the project manually:

#### Prerequisites for Windows

- Node.js (v22+) - [Download from nodejs.org](https://nodejs.org/)
- Python 3.12 - [Download from python.org](https://www.python.org/)
- Git for Windows - [Download from git-scm.com](https://git-scm.com/)
- Docker Desktop - [Download from docker.com](https://www.docker.com/products/docker-desktop/)

#### Manual Installation Steps

1. **Install dependencies:**

   ```powershell
   # Install root dependencies (for git hooks)
   npm install

   # Install frontend dependencies
   cd frontend
   npm install
   cd ..

   # Install backend dependencies (using virtual environment)
   cd backend
   python -m venv .venv
   # Activate virtual environment
   .venv\Scripts\activate  # On Windows
   # .venv/bin/activate    # On macOS/Linux if using this section
   pip install --upgrade pip
   pip install -r requirements.txt
   cd ..
   ```

2. **Set up git hooks:**

   ```powershell
   npx lefthook install
   ```

3. **Run the development servers:**

   ```powershell
   # Terminal 1 - Backend
   cd backend
   # Activate virtual environment first
   .venv\Scripts\activate
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2 - Frontend (in a new terminal)
   cd frontend
   npm run dev
   ```

**Note:** Remember to activate the virtual environment (`.venv\Scripts\activate`) every time you work with the backend in a new terminal session.

#### Alternative: Use WSL2 (Recommended)

For the best development experience on Windows, we recommend using WSL2:

1. Install WSL2 following [Microsoft's guide](https://docs.microsoft.com/en-us/windows/wsl/install)
2. Install Ubuntu or your preferred Linux distribution
3. Follow the standard Unix setup instructions above

This provides a native Linux environment where all the Makefile commands work as expected.

## Tech Stack

### Frontend

- [Vue.js 3](https://vuejs.org/) - Progressive JavaScript Framework
- [Quasar](https://quasar.dev/) - Vue.js Framework
- [ECharts](https://echarts.apache.org/) - Data Visualization
- [nginx](https://nginx.org/) - Web Server

### Backend

- [Python](https://www.python.org/) with FastAPI

### Infrastructure

- [Docker](https://www.docker.com/) - Containerization
- [Traefik](https://traefik.io/) - Edge Router

_Note: Update this section with your actual tech stack_

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Status

Under active development. [Report bugs here](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues).

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) - see the LICENSE file for details.

This is free software: you can redistribute it and/or modify it under the terms of the GPL-3.0 as published by the Free Software Foundation.

# Setup Checklist Completed

The following items from the original setup checklist have been automatically completed:

- [x] Replace `{ YOUR-REPO-NAME }` in all files by the name of your repo
- [x] Replace `{ YOUR-LAB-NAME }` in all files by the name of your lab
- [x] Replace `{ DESCRIPTION }` with project description
- [x] Replace assignees: githubusernameassignee by the github handle of your assignee
- [x] Handle CITATION.cff file (kept/removed based on preference)
- [x] Handle release-please workflow (kept/removed based on preference)
- [x] Configure project-specific settings

## Remaining Manual Tasks

Please complete these tasks manually:

- [x] Add token for the github action secrets called: MY_RELEASE_PLEASE_TOKEN (since you kept the release-please workflow)
- [x] Check if you need all the labels: https://github.com/EPFL-ENAC/leure-speed-to-zero/labels
- [x] Create your first milestone: https://github.com/EPFL-ENAC/leure-speed-to-zero/milestones
- [ ] Protect your branch if you're a pro user: https://github.com/EPFL-ENAC/leure-speed-to-zero/settings/branches
- [ ] [Activate discussion](https://github.com/EPFL-ENAC/leure-speed-to-zero/settings)

## Helpful links

- [How to format citations ?](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)
- [Learn how to use github template repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
