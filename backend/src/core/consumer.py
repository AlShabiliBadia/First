import json
from utils import get_redis_client
from config import settings




def start_consuming()
    r = get_redis_client()
    

    while True:
        # settings.QUEUE_PROCESSING

        # consuming the job from the main queue and moving it to the processing queue
        new_job = r.blmove(settings.QUEUE_MAIN, settings.QUEUE_PROCESSING, "RIGHT", "LEFT", timeout=0)

        try:
            job = json.loads(new_job)
            
            category = job.pop("category")
            data = job
            
            #TODO: call notifier(category, data)
            # we will call notifier to notify the user about the new job
            
        
            # removing the job from the processing queue
            r.lrem(settings.QUEUE_PROCESSING, 1, new_job)

        except Exception as e:
            print(f"CRASHED due to error: {e}")


