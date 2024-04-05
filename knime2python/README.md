# Knime2python converter

## Run Tests
- Select the test to run in the tests `node` or `workflow` folder
- Right-click and select 'Run'

# EUCalc API

## Prerequisites

- If using Knime as backend:
  * The Knime executable must be in the PATH variable and refer to the KNIME installation executable
  * A MySQL database instance is running
- Python 3.6 with relevant packages are installed (see `requirements.txt`) 
- The EUCalc "_interactions" repo has been cloned with a version compatible with this version of the converter and the API.
- To use the initialisation function of the API app, the individual sector repos also need to be cloned to have access to the raw input data.

## Using the EUCalc API

The EUCalc API app provides access to various features.
Run the "eucalc-app.py" file to get specific usage instructions.

### Initialising the API: simple method
The API app provides a functionality to recreate the files that represent intermediary (preprocessed) data. 
This uses the Knime workflow specified in the configuration.

### Starting the API
- Run `eucalc-app.py api` to create an API using Python as back-end. Upon startup, it will run a conversion of the Knime workflow defined in the configuration.
- Run `eucalc-app.py api -d` ("development" mode) to create an API using Knime as back-end. It uses the workflow specified in the configuration and is able to cache the output data in the database.

### Testing the API

Recommended software for testing:

- Firefox
- RESTED extension

Parameters to test:

- URL: composed of the host (such as http://127.0.0.1:5000/) followed by endpoint, currently 2 are defined:
    * api/v1.0/**levers** (GET)
    * api/v1.0/**results** (POST)

- See the /scripts folder for an example of an api request.

# Deployment to Docker on AWS

## Set up a build instance

Best is to use an Amazon Linux 2 instance on an EC2 server.
For convenience, you can give the EC2 instance a role that has `AmazonEC2ContainerRegistryFullAccess ` policy, so that the instance doesn't have to store AWS account credentials. 

## Configure the build instance

Follow recommendations at https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-basics.html.
Then:
- Copy ssh key for public access to this repo to ~/.ssh/climact_knime2python_bitbucket_rsa, and `chmod 600`
- Create config file with the following:       
```Host bitbucket.org
     Hostname bitbucket.org
     IdentityFile ~/.ssh/climact_knime2python_bitbucket_rsa
     IdentitiesOnly yes
```
- Install git `sudo yum install git`
- `git clone git@bitbucket.org:climact/knime2python.git`

## Build Docker images on the EC2 instance
To build the EUCalc API image: 

`docker build . --build-arg MODEL_VERSION=v1.3 -t 910931614638.dkr.ecr.eu-central-1.amazonaws.com/eucalc:1.6`.  
- Update the MODEL_VERSION with current version number or do not include argument, in which case "master" is used
- The -t argument specifies the repository and tag 

The repository (the part before the /) can be left blank if building only for the local machine. It can later be tagged with `docker tag image:tag image:tag`.

## Test Docker containers locally

`docker run -d --name api -p 5000:5000 910931614638.dkr.ecr.eu-central-1.amazonaws.com/eucalc:1.6`

-d option is to run in detached mode.
After having done this, the container can be started with `docker start api` and stopped with `docker stop api`.

Note: when restarting the server:
`sudo service docker start`

To view logs:
`docker logs api` or `docker logs -f api` for the live feed.

To view resource usage: `docker stats`

Additional versions of containers (e.g. to test) can be deployed by changing the port mapping and the container name: `docker run -d --name api-test -p 5001:5000 eucalc_api:1.3-test` (don't forget to allow the port in AWS VPC)

## Pushing the image to AWS ECR

### Setup
- In AWS ECS, create the repository `eucalc`
- Set up region `aws configure`, only answer the "region" question
- Get docker login `aws ecr get-login --no-include-email` and run the resulting command.

### Push to ECR
Tags are preserved on the server:

`docker push 910931614638.dkr.ecr.eu-central-1.amazonaws.com/eucalc:1.6`
# Deploying to AWS ECS
## Configure ECS
- Create a cluster, or use the default cluster
- Create a task definition
  * Network mode: awsvpc
  * Compatibility: Fargate (currently available in central-1)
  * Task role: only needed if containers need to call AWS services (not needed in our case)
  * Task execution role: this is a role that allows the ECS container agent (running on the instances) to issue calls to ECR (to pull containers) and to Cloudwatch to write logs. 
  We use `ecsTaskExecutionRole` (role with `AmazonECSTaskExecutionRolePolicy` permission and trust entity `ecs-tasks.amazonaws.com`)
  * Add the two containers, with port mapping 3306 for db. With Fargate, the containers in the same task will behave as if they were on the same machine: they can communicate through `localhost`  (therefore not `db` as with a local Docker). It seems adding the port mapping creates an error, but clicking "create task" a second time works.
- Create a VPC with a subnet and an IGW
  * Access only to 5000 (no 3306!)
- Start task in cluster, with parameters:
  * Fargate
  * The VPC and subnet defined before.


## Conda installation

0) pyenv install 3.6.12
1) conda create --name myenv python=3.6.13 anaconda=5.2
2) 