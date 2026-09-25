import logging
from dataclasses import dataclass, asdict


from processing.stages.clean_text import clean_text
from processing.stages.embed import EMBEDDING_RECIPE_VERSION
from processing.stages.extract import ExtractionError
from processing.stages.normalize import normalize
from processing.stages.validate import ValidationRejection, validate
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    processed: int = 0
    skipped: int = 0
    rejected :int = 0
    failed: int = 0
    
    def bump(self,outcome: str)-> None:
        setattr(self,outcome,getattr(self,outcome)+1)
    def as_dict(self)-> dict:
        return asdict(self)



class JobProcessor:
    def __init__(self, connection, raw_repo, processed_repo, extractor,embedder):
        self.conn = connection
        self.raw_repo = raw_repo
        self.processed_repo = processed_repo
        self.extractor = extractor
        self.embedder = embedder
    def process_one(self, raw_job : dict) -> str:
        raw_id = raw_job["id"]
        title = raw_job.get("title")
        try:
            cleaned = clean_text(raw_job.get("description"))
            extracted = self.extractor.extract(title,cleaned)
            validated = validate(extracted)
            processed = normalize(validated)
            embedding = self.embedder.embed(processed)
            
            new_id = self.processed_repo.insert(raw_id,processed,embedding, EMBEDDING_RECIPE_VERSION)
            self.raw_repo.mark_processed(raw_id)
            self.conn.commit()
            return "skipped" if new_id is None else "processed"
        except ValidationRejection as e:
            return self._quarantine(raw_id, f"rejected: {e}", "rejected", logging.INFO)
        except ExtractionError as e:
            return self._quarantine(raw_id, f"extraction: {e}", "failed", logging.WARNING)
        except Exception as e:  # never let one job kill the batch
            logger.exception("Unexpected error on raw_job %s", raw_id)
            return self._quarantine(raw_id, f"error: {e}", "failed", logging.ERROR)   



    def _quarantine(self, raw_id, error, outcome, level)-> str:
        self.conn.rollback()
        logger.log(level, "Raw job %s: %s", raw_id, error)
        self.raw_repo.mark_failed(raw_id, error)
        self.conn.commit()
        return outcome
