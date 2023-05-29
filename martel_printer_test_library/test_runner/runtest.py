import contextlib
import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional
from asyncio.subprocess import Process

from .. import environment
from ..environment import TestEnvironment
from martel_printer_test_library import environment


class TestInstance:
    def __init__(self, test_env: TestEnvironment) -> None:
        self._process: Optional[Process] = None

        self._stdout: Optional[asyncio.StreamReader] = None
        self._stderr: Optional[asyncio.StreamReader] = None

        self._environment_file = NamedTemporaryFile(delete=False)
        test_env.save(self._environment_file)
        self._environment_file.close()

    def __del__(self) -> None:
        self._environment_file.delete = True

    async def start(self) -> None:
        self._process = await asyncio.create_subprocess_exec(
            "poetry",
            "run",
            "robot",
            "--consolecolors",
            "ANSI",
            "--outputdir",
            "./output_testsuite_pcb",
            "--pythonpath",
            "./martel_test_library",
            "--variablefile",
            f"{Path(environment.__file__).absolute()};{self._environment_file.name}",
            "./testsuite_pcb",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._stdout = self._process.stdout
        self._stderr = self._process.stderr

    def kill(self) -> None:
        if self._process is not None:
            self._process.kill()

    async def is_running(self) -> bool:
        if self._process is None:
            return False

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._process.wait(), 1e-6)
        return self._process.returncode is None

    async def output(self):
        if self._stdout is None or self._stderr is None:
            raise StopAsyncIteration

        while await self.is_running():
            with contextlib.suppress(asyncio.TimeoutError):
                line: bytes = await asyncio.wait_for(self._stdout.readline(), 0.01)
                yield line.decode().removesuffix("\n")

            with contextlib.suppress(asyncio.TimeoutError):
                line: bytes = await asyncio.wait_for(self._stderr.readline(), 0.01)
                yield line.decode().removesuffix("\n")
