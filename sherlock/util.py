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

import sys

from loguru import logger

class MyFilter:
    def __init__(self, level:str) -> None:
        self.level = level

    def __call__(self, record):
        return record["level"].no >= logger.level(self.level).no

def set_log(level:str) -> None:
    logger.remove(0)
    my_filter = MyFilter(level)
    logger.add(sys.stderr, filter=my_filter, level=level)