build:
	docker build -t externalstructureproxy .

server:
	docker run --rm -d -p 5010:5000 --rm --name externalstructureproxy externalstructureproxy /app/run_production_server.sh

interactive:
	docker run --rm -it -p 5010:5000 --rm --name externalstructureproxy externalstructureproxy /app/run_production_server.sh

dev-server:
	docker run --rm -it -p 5010:5000 --rm --name externalstructureproxy externalstructureproxy /app/run_server.sh

bash:
	docker run --rm -it -p 5010:5000 --rm --name externalstructureproxy externalstructureproxy bash

server-compose-build:
	docker-compose --compatibility build

server-compose-background:
	docker-compose --compatibility build
	docker-compose --compatibility up -d

server-compose-interactive:
	docker-compose --compatibility build
	docker-compose --compatibility up

server-compose-production:
	docker-compose --compatibility build
	docker-compose -f docker-compose.yml -f docker-compose-production.yml --compatibility up -d

server-compose-production-interactive:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-production.yml --compatibility up

init_modules:
	git submodule update --init --recursive

attach-library:
	docker exec -i -t externalstructureproxy-library_generation_worker /bin/bash
