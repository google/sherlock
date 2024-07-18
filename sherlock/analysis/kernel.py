import dataclasses


@dataclasses.dataclass
class Process:
  """Process structure."""
  pid: int
  uid: int
  upid: int
  parent_upid: int
  name: str
  cmdline: str
  path: str
  device: str
  reason: str


@dataclasses.dataclass
class ProcessLoop:
  """Process structure with loop information."""
  cnt: int
  process: Process


def extractProcesses(tp):
    qrit = tp.query(
        "SELECT p.upid, p.pid, p.name, p.parent_upid, p.uid, p.cmdline "
        "FROM process AS p ")
    for idx in range(0, len(qrit)):
        _upid, _pid, _name, _parent_upid, _uid, _cmdline, _path, _device = (
           qrit.upid[idx], qrit.pid[idx], qrit.name[idx], qrit.parent_upid[idx], qrit.uid[idx], qrit.cmdline[idx], qrit.path[idx], qrit.device[idx]
        )
        yield Process(_pid, _uid, _upid, _parent_upid, _name, _cmdline, _path, _device)


def extractProcessChildren(tp, device, pid):
    qrit = tp.query(
        "SELECT * "
        "FROM process "
        "WHERE parent_upid = %s" % pid)
    for idx in range(0, len(qrit)):
        if qrit.device[idx] == device:
            yield qrit

def findProcessName(tp, name):
    qrit = tp.query(
        'SELECT p.upid, p.pid, t.utid, t.tid, p.name, p.parent_upid, p.uid, p.cmdline '
        'FROM process AS p, thread AS t '
        'WHERE '
        'p.cmdline like \'%%%s%%\'' % name)
    for idx in range(0, len(qrit)):
        yield qrit

def detectSuspiciousChildren(tp) -> list[ProcessLoop]:
    suspicous_loop = []

    qrit = tp.query('select count(p.pid) as cntpids, p.parent_upid, p.uid from process as p GROUP BY p.parent_upid')
    for idx in range(0, len(qrit)):
        _cntpids, _parent_upid, _uid, _path, _device = qrit.cntpids[idx], qrit.parent_upid[idx], qrit.uid[idx], qrit.path[idx], qrit.device[idx]
        if _cntpids > 400:
            suspicous_loop.append(ProcessLoop(_cntpids, Process(-1, _uid, _parent_upid, -1, '', '',  _path, _device, 'Suspicious number of children')))
    return suspicous_loop

def detectPrivilegeEscalation(tp) -> list[Process]:
    qrit = tp.query(
        "SELECT p.upid, p.pid, t.utid, t.tid, p.name, p.parent_upid, p.uid, p.cmdline "
        "FROM process AS p, thread AS t "
        "WHERE "
        "p.uid = 0 "
        "AND p.parent_upid IN (SELECT upid FROM process WHERE uid != 0 AND upid = p.parent_upid) "
        "AND p.upid == t.upid")
    
    suspicous_pids = []
    for idx in range(0, len(qrit)):
        _upid, _pid, _utid, _tid, _name, _parent_upid, _uid, _cmdline, _path, _device = (
           qrit.upid[idx], qrit.pid[idx], qrit.utid[idx], qrit.tid[idx], qrit.name[idx], qrit.parent_upid[idx], qrit.uid[idx], qrit.cmdline[idx], qrit.path[idx], qrit.device[idx]
        )
        suspicous_pid = Process(_pid, _uid, _upid, _parent_upid, _name, _cmdline, _path, _device, "Privilege Esclation to uid=0")
        suspicous_pids.append(suspicous_pid)
    return suspicous_pids

def detectPrivilegeProcess(tp) -> list[Process]:
    qrit = tp.query(
        "SELECT p.upid, p.pid, p.name, p.parent_upid, p.uid, p.cmdline "
        "FROM process AS p "
        "WHERE "
        "p.uid = 0 and p.pid > 10000")
    
    suspicous_pids = []
    for idx in range(0, len(qrit)):
        _upid, _pid, _name, _parent_upid, _uid, _cmdline, _path, _device = (
           qrit.upid[idx], qrit.pid[idx], qrit.name[idx], qrit.parent_upid[idx], qrit.uid[idx], qrit.cmdline[idx], qrit.path[idx], qrit.device[idx]
        )
        suspicous_pid = Process(_pid, _uid, _upid, _parent_upid, _name, _cmdline, _path, _device, "Privilege process uid=0")
        suspicous_pids.append(suspicous_pid)
    return suspicous_pids

class SuspiciousBehavior:
    def __init__(self, tp, behavior_detector_list) -> None:
        self.tp = tp

        self.pids = []
        for behavior_detector in behavior_detector_list:
            self.pids.extend(behavior_detector(tp))