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

### Installing Development Tools (Optional but Recommended)

For better version management and faster package installation, you can install these tools:

#### Install Node Version Manager (nvm)

```bash
# Install nvm for Node.js version management
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# Restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc

# Install and use Node.js v22
nvm install 22
nvm use 22
```

#### Install uv (Fast Python Package Manager)

```bash
# Install uv for faster Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal or add to PATH
source ~/.bashrc  # or ~/.zshrc
```

#### Install pyenv (Python Version Manager)

```bash
# Install pyenv for Python version management
curl -fsSL https://pyenv.run | bash

# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc

# Install Python 3.12
pyenv install 3.12
pyenv global 3.12
```

**Note:** After installing these tools, restart your terminal or source your shell profile to use them.

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

#### Enabling Redis for Backend Caching

To enable Redis for caching in the backend, follow these steps:

1. **Start Redis using Docker Compose:**

   ```bash
   # Start Redis service in the background
   docker compose up -d redis
   ```

2. **Verify Redis is running:**

   ```bash
   # Check if Redis container is running
   docker ps | grep redis

   # Test Redis connection (optional)
   docker exec -it $(docker ps -q -f name=redis) redis-cli ping
   ```

3. **Configure the backend to use Redis:**

   The backend application should automatically detect and connect to Redis when it's available. If you need to configure Redis settings, check the backend configuration files in `backend/config/`.

4. **Stop Redis when done:**

   ```bash
   # Stop Redis service
   docker compose down redis

   # Or stop all services
   docker compose down
   ```

**Note:** Redis caching will improve the performance of the backend by storing frequently accessed data in memory. The backend will work without Redis, but with caching disabled.

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

#### WSL2 Troubleshooting

If you encounter line ending issues when using WSL2 (like `/usr/bin/env: 'bash\r': No such file or directory`), this is due to Windows line endings (CRLF) being used instead of Unix line endings (LF). Here are the solutions:

**Option 1: Configure Git to handle line endings automatically (Recommended)**

```bash
# Configure Git to automatically convert line endings
git config --global core.autocrlf input

# Re-clone the repository or reset line endings
git rm --cached -r .
git reset --hard
```

**Option 2: Convert line endings manually**

```bash
# Install dos2unix if not available
sudo apt update && sudo apt install dos2unix

# Convert line endings for the Makefile
dos2unix Makefile

# Convert line endings for all shell scripts (if any)
find . -name "*.sh" -exec dos2unix {} \;
```

**Option 3: Use .gitattributes file**

The repository should include a `.gitattributes` file to enforce consistent line endings. If it doesn't exist, create one:

```bash
# Create .gitattributes file
cat > .gitattributes << 'EOF'
* text=auto
*.sh text eol=lf
Makefile text eol=lf
*.py text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.vue text eol=lf
EOF

# Apply the changes
git add .gitattributes
git rm --cached -r .
git reset --hard
```

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
