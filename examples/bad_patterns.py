
import requests, logging
items = list(range(1000))

for x in range(100):
    logging.debug(f"value is {x}")  # lazy logging recommended

for i in items:
    if i in items:                   # set membership recommended
        pass

for url in ["https://example.com"]*5:
    requests.get(url)                # batch/parallelise recommended
