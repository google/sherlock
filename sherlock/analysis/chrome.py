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

from loguru import logger

import tldextract

import dataclasses
import os

@dataclasses.dataclass
class JSScript:
  """Javascript file representation."""
  id: int
  url: str
  source: str
  device: str
  path: str

def extractJsFiles(tp):
    logger.info('Extracting JS files from devices')

    qrit = tp.query('SELECT * FROM __intrinsic_v8_js_script')
    for idx in range(0, len(qrit)):
        _id, _type, _v8_isolate_id, _internal_script_id, _script_type, _name, _source, _path, _device = (
            qrit.id[idx], qrit.type[idx], qrit.v8_isolate_id[idx], qrit.internal_script_id[idx], qrit.script_type[idx], qrit.name[idx], qrit.source[idx], qrit.path[idx], qrit.device[idx]
        )
        if _script_type != 'NORMAL':
            continue
        yield JSScript(_id, _name, _source, _device, _path)

def extractAndSaveJsFiles(tp, output_dir):
    logger.info('Saving JS files from devices to ' + output_dir)

    for js_script in extractJsFiles(tp):
        domain = 'sherlock_unknown_domain'
        js_script_name = str(js_script.id) + '.js'

        if js_script.url:
            domain = tldextract.extract(js_script.url).registered_domain
            js_script_name = os.path.basename(js_script.url)

        if '.js' not in js_script_name:
            js_script_name = str(js_script.id) + '.js'

        dir_domain_path = os.path.join(output_dir, js_script.device, 'js', domain)
        try:
            os.makedirs(dir_domain_path)
        except FileExistsError as _:
            pass

        file_path = os.path.join(dir_domain_path, js_script_name)
        with open(file_path, 'w') as f:
            logger.debug('Saving js file ' + file_path)
            f.write(js_script.source)
