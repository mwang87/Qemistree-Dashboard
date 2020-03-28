build:
	docker build -t ioda .

bash:
	docker run -it -v $(PWD):/app --rm --name ioda ioda bash

server-compose-build-nocache:
	docker-compose build --no-cache

server-compose-interactive:
	docker-compose build
	docker-compose up

server-compose:
	docker-compose build
	docker-compose up -d

server-compose-production:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-production.yml up -d


attach:
	docker exec -i -t ioda-worker1 /bin/bash
