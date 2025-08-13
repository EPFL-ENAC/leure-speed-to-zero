# Python Calculator

**Authors**: Dr. Gino Baudry (EPFL, gino.baudry[at]epfl.ch), Dr. Paola Paruta (EPFL, paola.paruta[at]epfl.ch), Dr. Edoardo Chiarotti (E4S, edoardo.chiarotti[at]epfl.ch), Agathe Crosnier (EPFL, agathe.crosnier[at]epfl.ch).

## Step by step installation

In order to run PathwayCalc you first need to:

### Step 1: Model database

Get the data from
<a href="https://drive.google.com/drive/u/1/folders/1UrYny7mcWQuBrL6KdOKrfEQEkwU0vV8E" target="_blank"> Google Drive</a> (2050-Calculator's drive)
Extract the dataset in the following folder: _YourWorkspace/database/data_
Go to the google drive EPFL-Calc, there navigate to PathwayCalc/database/ here you find the a zipped data folder.
You need to download it and extract it in your local directory PathwayCalc/\_database with name "data".
Inside you should see the folders csv, xls, datamatrix. The folder datamatrix contains the empty subfolder geoscale.

### Step 2: Virtual Envioronment

Create a virtual environment (do once for all). The virtual environment is to be created using the file requirements.txt. In PyCharm, you can create a Python environment using a _requirements.txt_ file by following these steps:

#### Open PathwayCalc as a project in PyCharm

Access project settings: Navigate to the project settings by clicking on File -> Settings (on Windows/Linux) or PyCharm -> Preferences (on macOS).

#### Configure Python interpreter:

In the settings window, find the Project: <Your Project Name> section and select Python Interpreter under it. Click on the gear icon on the top-right corner of the Python interpreter dropdown and select Add.

#### Choose new environment:

In the Add Python Interpreter dialog, choose Virtualenv Environment, Pipenv Environment, or Conda Environment, depending on your preference. For this example, I'll use Virtualenv Environment.

#### Select base interpreter:

Choose the base interpreter (the Python interpreter you want to use) from the dropdown.If you don't have one installed, you can install it by clicking on the three dots (...) and selecting New Environment. Choose Python 3.9 which is compatible with the other requirements. An example for location of your interpreter is PathwayCalc/venv, and an example for the interpreter name is usr/local/bin/python3.9. Click OK. This action will create a folder in your project repository, where the interpreter is and packages will be saved (if the name of your interpreter is PathwayCalc/venv, this folder will be called "venv").

#### Specify requirements file:

Close the preferences window, then go to Tools and open Sync python requirements. In the first option "Package requirement file", select the file requirements.txt that you have in the project's folder. Its path will look something like .../PathwayCalc/requirements.txt. In the second option "Version in requirements", select "strong equality". And of the remaining options, select only the last one "keep existing version specifier". Once this is set, open the file .../PathwayCalc/requirements.txt with PyCharm (just double click on it in the Project's files). As you open it, PyCharm should then suggest you to install the missing packages (if it does not, go to Preferences -> Editor -> Inspector -> Unsatisfied package requirements -> Click the box and reset). Install the packages, this may take a few moments.

#### Check environment:

Once the download is complete, you can go back to settings and click Project: <Your Project Name> -> Python Interpreter. The name of the interpreter should be something like "Python 3.9 (name of your project)" and below you should see the full list of pacakges just downloaded. You can check that they correspond to the ones mentioned in .../PathwayCalc/requirements.txt. If they do not, repeat the steps above.

### Step 3: Configuration

Go to _knime2python/config/_ if you don't see a _config_eu.yml_, copy & paste _config_example.yml_
and rename it as config_eu.yml. Then, in the file you will find 3 paths that you need to change manually to match your local workspace.

#### Regional Configuration

The application uses a centralized configuration file `model_config.json` in the project root to manage regional data settings:

```json
{
  "MODEL_PRIMARY_REGION": "Vaud",
  "AVAILABLE_REGIONS": ["Vaud", "Switzerland", "EU27"]
}
```

### Step 4: Modern Development Setup (Recommended)

The modern development setup uses the Makefile and supports both `uv` (fast) and traditional Python virtual environments:

#### Quick Start

```bash
# Install dependencies (automatically detects uv or creates .venv)
make install

# Run the development server
make run

# The API will be available at:
# - Backend: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
```

#### Available Commands

```bash
make install    # Install dependencies using uv or pip
make run        # Start development server with auto-reload
make format     # Format code with black
make lint       # Run linting checks
make test       # Run tests
make cleanup    # Clean up lingering processes
```

#### Manual Setup (Alternative)

If you prefer manual setup or are using an IDE like PyCharm:

1. **Create virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Step 5: Legacy Instructions (PyCharm - Optional)

For users who prefer PyCharm IDE setup, you can follow the traditional virtual environment setup:

1. **Open the project in PyCharm**
2. **Configure Python interpreter** (File > Settings > Project > Python Interpreter)
3. **Create virtual environment** and install requirements.txt
4. **Run the FastAPI application** using uvicorn

**Note:** The modern Makefile approach (Step 4) is recommended as it's simpler and more reliable.

## API Documentation

Once the server is running, you can access:

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

## Region-Specific Data

The application automatically loads data for the region specified in `model_config.json`. Ensure your data directory contains the required pickle files for the selected region:

- `_database/data/datamatrix/` should contain region-specific data files
- Cache will automatically namespace data by region to prevent conflicts

```
http://127.0.0.1:8080/app
```

In the menu on the left, you can change the ambition criteria of each section. The emission pathways should change consequently. Have fun exploring the pathways!
