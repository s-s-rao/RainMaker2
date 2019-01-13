docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)
docker rmi $(docker images -f "dangling=true" -q)
docker network rm RainMakerNetwork
docker ps -a
docker image ls
echo "Reset complete!"