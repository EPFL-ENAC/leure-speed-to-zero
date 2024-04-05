curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose

#sudo apt-get update \
#&& sudo apt-get install -y \
#	    apt-transport-https \
#	    ca-certificates \
#	    curl \
#	    gnupg-agent \
#	    software-properties-common \
#&& curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - \
#&& sudo add-apt-repository \
#	   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
#	   $(lsb_release -cs) \
#	   stable" \
#&& sudo apt-get update \
#&& sudo apt-get install -y docker-ce \
#&& sudo docker run hello-world \
#&& sudo apt-get install -y docker-compose

