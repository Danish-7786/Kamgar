import pytest

from processing.schemas import ProcessedJob, Seniority
from processing.stages.embed import JobEmbedder
from processing.pipeline import JobProcessor
from unittest.mock import Mock


def job():
    return ProcessedJob(role='Backend Engineer', seniority=Seniority.ENTRY, skills=['Python'])


@pytest.mark.parametrize('vectors', [[[1.0]], [[float('nan')] * 384], [[0.0] * 384], []])
def test_invalid_encoder_output(vectors):
    encoder = Mock()
    encoder.encode.return_value = vectors
    with pytest.raises(ValueError):
        JobEmbedder(encoder).embed(job())


def test_valid_vector_and_empty_batch():
    encoder = Mock()
    encoder.encode.return_value = [[1.0] * 384]
    embedder = JobEmbedder(encoder)
    assert embedder.embed(job()) == [1.0] * 384
    encoder.reset_mock()
    assert embedder.embed_many([]) == []
    encoder.encode.assert_not_called()


def test_processing_failure_rolls_back_before_recording_failure():
    events = Mock()
    extractor = Mock()
    extractor.extract.side_effect = RuntimeError('unavailable')
    processor = JobProcessor(events.conn, events.raw, Mock(), extractor, Mock())
    assert processor.process_one({'id': 1, 'title': 'Engineer', 'description': 'Python developer'}) == 'failed'
    assert [call[0] for call in events.mock_calls] == ['conn.rollback', 'raw.mark_failed', 'conn.commit']
