
PERFETTO_CMD = 'perfetto'
DEVICE_DIR = '/data/misc/perfetto-traces/'

class Config:
    def __init__(self, filename, output_dir, perfetto_cmd=PERFETTO_CMD, device_dir=DEVICE_DIR) -> None:
        self.filename = filename
        self.output_dir = output_dir
        
        self.perfetto_cmd = perfetto_cmd
        self.device_dir = device_dir