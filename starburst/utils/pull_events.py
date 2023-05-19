from kubernetes import client, config
#import logger 
import time 
import logging
#client.rest.logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def save_events(onprem_cluster="gke_sky-burst_us-central1-c_skyburst-gpu", cloud_cluster="gke_sky-burst_us-central1-c_skyburst-gpu-cloud"):
    config.load_kube_config(context=onprem_cluster)
    onprem_api = client.CoreV1Api()

    config.load_kube_config(context=cloud_cluster)
    cloud_api = client.CoreV1Api()

    with open("./events.log", "w") as f:
        while True: 
            clusters = {"onprem": onprem_api, "cloud": cloud_api}
            for type in clusters:
                api = clusters[type]
                if api is not None:
                    events = api.list_event_for_all_namespaces()
                    f.write(str(events).replace('\n',' ') + "\n")
            time.sleep(3)
    return 