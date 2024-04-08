# Python Calculator 
**Authors**: Dr. Gino Baudry (EPFL, gino.baudry[at]epfl.ch), Dr. Paola Paruta (EPFL, paola.paruta[at]epfl.ch).

## Step by step installation
In order to run PathwayCalc you first need to:

### Step 1: Model database

Get the data from
<a href="https://drive.google.com/drive/u/1/folders/1UrYny7mcWQuBrL6KdOKrfEQEkwU0vV8E" target="_blank"> Google Drive</a> (2050-Calculator's drive)
Extract the dataset in the following folder: *YourWorkspace/_database/data*
Go to the google drive EPFL-Calc, there navigate to PathwayCalc/_database/ here you find the a zipped data folder.
You need to download it and extract it in your local directory PathwayCalc/_database with name "data".
Inside you should see the folders csv, xls, datamatrix. The folder datamatrix contains the empty subfolder geoscale.

### Step 2: Virtual Envioronment
Create a virtual environment (do once for all). The virtual environment is to be created using the file requirements.txt. In PyCharm, you can create a Python environment using a *requirements.txt* file by following these steps:

#### Open PathwayCalc as a project in PyCharm

Access project settings: Navigate to the project settings by clicking on File -> Settings (on Windows/Linux) or PyCharm -> Preferences (on macOS).

#### Configure Python interpreter: 
In the settings window, find the Project: <Your Project Name> section and select Python Interpreter under it. Click on the gear icon on the top-right corner of the Python interpreter dropdown and select Add.

#### Choose new environment: 
In the Add Python Interpreter dialog, choose Virtualenv Environment, Pipenv Environment, or Conda Environment, depending on your preference. For this example, I'll use Virtualenv Environment.

#### Select base interpreter: 
Choose the base interpreter (the Python interpreter you want to use) from the dropdown.If you don't have one installed, you can install it by clicking on the three dots (...) and selecting New Environment or Existing Environment, depending on your preference. Choose Python 3.9 which is compatible with the other requirements.

#### Specify requirements file: 
In the Create Virtual Environment dialog, select Existing environment, and then click on the folder icon next to the Location field to navigate to the directory containing your requirements.txt file. Choose requirements.txt: Navigate to and select your requirements.txt file. Create environment: Click OK to create the virtual environment using the packages listed in your requirements.txt file. Wait for environment creation: PyCharm will now create the virtual environment and install the packages listed in your requirements.txt file. This may take a few moments.

#### Confirm environment: 

Once the process is complete, you'll see your new environment listed in the Python interpreter dropdown. Select it and click OK to confirm. Your project will now use the virtual environment created from the requirements.txt file, ensuring that you have the correct dependencies installed for your project.

### Step 3: Configuration file:

Go to *knime2python/config/* if you don't see a *config_eu.yml*, copy & paste *config_example.yml*
and rename it as config_eu.yml, then edit the paths to match your local workspace.

### Step 4: Local server
Open a terminal, navigate to PathwayCalc/transition-pathway-explorer and run 

```
npm run serve
```
(One needs to install it when used for the very first time, i.e. Node JS and NPM)

### Step 5: Converter knime to python 
In PyCHarm, run *knime2python/scripts/eucalc-app.py*

### Step 6: TPE (transition pathway explorer)
Open your browser (do not use safari) at the address: 

```
http://127.0.0.1:8080/app
```
    
For the moment the only output that works is Transport 'Passenger distance by mode', and it changes using the lever *'key behaviours/travel'*
