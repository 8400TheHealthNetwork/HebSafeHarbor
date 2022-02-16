import threading
from enum import Enum
from typing import Dict, List

from hebsafeharbor import HebSafeHarbor


class ServiceStatus(Enum):
    UNINITIALIZED = 1
    LOADING = 2
    READY = 3
    ERROR = 4


class HebSafeHarborService:
    def __init__(self):
        self.hch: HebSafeHarbor = None
        self.status = ServiceStatus.UNINITIALIZED

    def _initialize(self):
        self.status = ServiceStatus.LOADING
        try:
            hch = HebSafeHarbor()

            doc = hch(
                [{"id": "id", "text": "גדעון לבנה הגיע ב16.1.2022 לבית החולים שערי צדק עם תלונות על כאבים בחזה"}])

            self.status = ServiceStatus.READY
            self.hch = hch
            print("Hebrew Safe Harbor Service is up and ready to serve")

        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise e

    def load_async(self):
        if self.status == ServiceStatus.UNINITIALIZED:
            load_model_thread = threading.Thread(
                target=hsh_service._initialize)
            load_model_thread.start()

    def ready(self):
        if self.status == ServiceStatus.READY:
            readiness, status_code = "ready", 200
        elif self.status in [ServiceStatus.UNINITIALIZED, ServiceStatus.LOADING]:
            readiness, status_code = "unready", 503
        else:  # self.status == ServiceStatus.ERROR:
            readiness, status_code = "unready", 500
        return {
                   "service": "Hebrew Safe Harbor",
                   "status": readiness
               }, status_code

    def query(self, docs: List[Dict[str, str]]):
        # executing the prediction
        try:
            output_docs = self.hch(docs)
            return output_docs, 200
        except Exception as e:
            return f"Bad response: {e}", 400


hsh_service = HebSafeHarborService()
