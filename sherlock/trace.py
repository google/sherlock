# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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