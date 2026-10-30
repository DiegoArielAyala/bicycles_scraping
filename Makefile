worker:
	docker compose -f docker/docker-compose.yml up -d worker
worker-logs:
	docker compose -f docker/docker-compose.yml logs -f worker
worker-shell:
	docker compose -f docker/docker-compose.yml exec worker python manage.py shell

scraper2:
	python3 -m scripts.run_scraper --start 1 --end 2 --web biking_point --delete

scraper20:
	python3 -m scripts.run_scraper --start 1 --end 20 --web biking_point --delete

test:
	python3 manage.py test apps.catalog.test.test_create_new_bicycles