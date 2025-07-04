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

### Step 3: Configuration file:

Go to _knime2python/config/_ if you don't see a _config_eu.yml_, copy & paste _config_example.yml_
and rename it as config_eu.yml. Then, in the file you will find 3 paths that you need to change manually to match your local workspace.

### Step 4: Local server

Open a terminal, navigate to PathwayCalc/transition-pathway-explorer and run

```
npm run serve
```

(One needs to install it when used for the very first time, i.e. Node JS and NPM.
Download node js version v16.17.0 https://nodejs.org/download/release/v16.17.0/. Download the .msi file.
Go to PathwayCalc/transition-pathway-explorer and run

```
npm install
```

)

### Step 5: Converter knime to python

In PyCHarm, run _knime2python/scripts/eucalc-app.py_

### Step 6: TPE (transition pathway explorer)

Open your browser (do not use safari) at the address:

```
http://127.0.0.1:8080/app
```

In the menu on the left, you can change the ambition criteria of each section. The emission pathways should change consequently. Have fun exploring the pathways!
