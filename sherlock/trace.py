from perfetto.batch_trace_processor.api import BatchTraceProcessor
from perfetto.trace_uri_resolver.resolver import TraceUriResolver

from loguru import logger

class GenerateTraceConfig:
    def __init__(self) -> None:
        pass
    
class CustomResolver(TraceUriResolver):
    def __init__(self, raw_traces):
        self.raw_traces = raw_traces

    def resolve(self):
        return [
           TraceUriResolver.Result(trace=self.raw_traces[device], metadata={ 'path': self.raw_traces[device], 'device': device }) for device in self.raw_traces
        ]

class Traces:
    def __init__(self, raw_traces) -> None:
        logger.debug(raw_traces)
        self.devices = raw_traces.keys()
        self.btp = BatchTraceProcessor(CustomResolver(raw_traces))

    def query(self, sql):
        return self.btp.query_and_flatten(sql)