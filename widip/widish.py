from multiprocessing import Pipe
from pathlib import Path
from subprocess import PIPE, Popen
import sys

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.frobenius import Hypergraph as H, Id, Spider
from discopy import python

from .files import stream_diagram



class IORun(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        def step(*processes: IOProcess):
            """
            A many-to-many pipe.
            """
            assert typ == Ty("io")
            assert len(processes) == n_legs_in
            if not processes:
                return ((), ) * n_legs_out
            return (IOSpiderProcess(*(processes[0], )), ) * n_legs_out
        return IORun(
            inside=step,
            dom=Ty(*("io" for _ in range(n_legs_in))),
            cod=Ty(*("io" for _ in range(n_legs_out))))


def command_io_f(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    def command_io(b):
        return (
            H.spiders(len(b.dom), 1, Ty("io")).to_diagram() @ H.spiders(0, 1, b.dom).to_diagram() >>
            Box(b.name,
                Ty("io") @ b.dom,
                Ty("io")) >>
            # TODO splitting into len(cod) copies more than needed
            H.spiders(1, len(b.cod), Ty("io")).to_diagram())
    f = Functor(
        lambda x: Ty("io"),
        lambda b: command_io(b),)
    diagram = f(diagram)
    return (
        H.spiders(0, 1, diagram.dom).to_diagram() >>
        diagram >>
        H.spiders(len(diagram.cod), 1, Ty("io")).to_diagram())


class IOProcess:
    """mutual with IOSpiderProcess"""
    def __init__(self, box, *spider_processes):
        assert box.dom[0] == Ty("io")
        assert box.cod == Ty("io")
        self.spider_processes = spider_processes
        self.popen_args = [box.name, *("" if t == Ty() else t.name for t in box.dom[1:])]
        self.pipe_in, self.pipe_out = Pipe(duplex=False)

    def communicate(self, input):
        # print("process:", self.spider_processes)
        # i = self.pipe_in.recv()
        o = ""
        for p in self.spider_processes:
            o += p.communicate(input)
        # print(o, self.popen_args)
        popen = Popen(self.popen_args, stdin=PIPE, stdout=PIPE, text=True)
        (o, _) = popen.communicate(o)
        # print(o, self.popen_args)
        return o


class IOSpiderProcess:
    """
    takes many processes and creates n copies of their joined outputs
    mutual with IOSpider"""
    def __init__(self, *processes: IOProcess):
        self.processes = processes
        self.pipe_in, self.pipe_out = Pipe(duplex=False)

    def communicate(self, input):
        # print("spiderprocess:", [p.popen for p in self.processes])
        w = ""
        for p in self.processes:
            o = p.communicate(input)
            w += o
        return w

shell_f = Functor(
    lambda x: Ty("io"),
    lambda b: lambda *p: IOProcess(b, *p),
    cod=Category(Ty, IORun))


def widish_main(file_name):
    path = Path(file_name)
    diagram = stream_diagram(path.open())
    diagram = command_io_f(diagram)
    diagram.draw(path=path.with_suffix(".jpg"))
    process: IOSpiderProcess = shell_f(diagram)()
    r = process.communicate("")
    sys.stdout.write(r)
