from prometheus_client import Counter
from prometheus_client import Gauge


# initialise a prometheus counter
class Metrics:
    w3w_api_calls = Counter(
        "w3w_api_calls", "total number of calls to the What 3 Words API"
    )
