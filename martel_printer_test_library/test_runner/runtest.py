import asyncio
from pathlib import Path
import signal
import subprocess
from tempfile import NamedTemporaryFile
from typing import Optional
from asyncio.subprocess import Process
from asyncio.queues import Queue

from .. import environment
from ..environment import TestEnvironment


class TestInstance:
    def __init__(self, test_env: TestEnvironment, tags: list[str]) -> None:
        self._process: Optional[Process] = None

        self._stdout: Optional[asyncio.StreamReader] = None
        self._stderr: Optional[asyncio.StreamReader] = None

        self._environment_file = NamedTemporaryFile(delete=False)
        test_env.save(self._environment_file)
        self._environment_file.close()

        self._test_tags: list[str] = tags

        self.test_output: Queue = Queue()

    def __del__(self) -> None:
        self._environment_file.delete = True

    async def run(self, log_level: str = "INFO"):
        command = [
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
        ]
        command.extend(["--loglevel", log_level])

        print(self._test_tags)

        for tag in self._test_tags:
            command.extend(["--include", tag])

        command.append("./testsuite_pcb")

        print(f"Running test with command: {command}")

        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        self._stdout = self._process.stdout
        self._stderr = self._process.stderr

        async for line in self.output():
            await self.test_output.put(line)

        await self._process.wait()

    def kill(self) -> None:
        if self._process is not None:
            self._process.send_signal(signal.CTRL_BREAK_EVENT)

    async def output(self):
        if self._process is None or self._stdout is None or self._stderr is None:
            raise StopAsyncIteration

        while self._process.returncode is None:
            done, remaining = await asyncio.wait(
                [
                    asyncio.Task(self._stdout.readline(), name="stdout"),
                    asyncio.Task(self._stderr.readline(), name="stderr"),
                    asyncio.Task(self._process.wait(), name="complete"),
                ],
                return_when="FIRST_COMPLETED",
            )

            for task in remaining:
                task.cancel()

            for task in done:
                if task.get_name() == "complete":
                    break

                if task.get_name() == "stdout" or task.get_name() == "stderr":
                    result = task.result()
                    if type(result) is bytes:
                        yield result.decode().removesuffix("\n")
