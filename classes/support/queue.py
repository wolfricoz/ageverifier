import asyncio
import inspect
import logging
import math

import discord
from discord_py_utilities.exceptions import NoPermissionException

from classes.singleton import Singleton
from databases.exceptions.KeyNotFound import KeyNotFound


def describe_task(task, include_args: bool = False) -> str:
    """Best-effort, human-readable description of a queued task for logging.

    For coroutines this digs into the object so a queue error points back to the real
    call site instead of just "send_message": the qualified name, the source
    file:line where the coroutine was created, its run state, and — when
    ``include_args`` is set — the arguments still held in the (not-yet-started)
    frame. Capture this BEFORE awaiting: once the coroutine finishes, cr_frame is
    gone and the arguments with it. Everything is wrapped defensively so describing a
    task can never raise inside the error handler.
    """
    try:
        name = getattr(task, "__qualname__", None) or getattr(task, "__name__", None) or repr(task)
        if not inspect.iscoroutine(task):
            return name

        parts = [name]
        code = getattr(task, "cr_code", None)
        if code is not None:
            parts.append(f"({code.co_filename}:{code.co_firstlineno})")
        try:
            parts.append(f"[{inspect.getcoroutinestate(task)}]")
        except Exception:
            pass

        if include_args:
            frame = getattr(task, "cr_frame", None)
            f_locals = getattr(frame, "f_locals", None) if frame is not None else None
            if f_locals:
                rendered_args = []
                for key, value in f_locals.items():
                    if key == "self":
                        continue
                    try:
                        rendered = repr(value)
                    except Exception:
                        rendered = f"<unrepresentable {type(value).__name__}>"
                    if len(rendered) > 200:
                        rendered = rendered[:200] + "…"
                    rendered_args.append(f"{key}={rendered}")
                if rendered_args:
                    parts.append("args(" + ", ".join(rendered_args) + ")")

        return " ".join(parts)
    except Exception as e:
        return f"{getattr(task, '__name__', repr(task))} <describe failed: {e}>"


class Queue(metaclass=Singleton):
    high_priority_queue = []
    normal_priority_queue = []
    low_priority_queue = []
    task_finished = True

    def clear(self) :
        self.high_priority_queue = []
        self.normal_priority_queue = []
        self.low_priority_queue = []
        self.task_finished = True

    def status(self) :
        return f"Remaining queue: High: {len(self.high_priority_queue)} Normal: {len(self.normal_priority_queue)} Low: {len(self.low_priority_queue)} Estimated time: {round(math.ceil(self.get_queue_time()) / 60, 2)} minutes"

    def empty(self):
        return len(self.high_priority_queue) == 0 and len(self.normal_priority_queue) == 0 and len(self.low_priority_queue) == 0

    def add(self, task, priority: int = 1) -> float:
        """Adds a task to the queue with a priority of high(2), normal(1), or low(0)"""
        # noinspection PyUnreachableCode
        match priority:
            case 2:
                self.high_priority_queue.append(task)
            case 1:
                self.normal_priority_queue.append(task)
            case 0:
                self.low_priority_queue.append(task)
            case _:
                self.normal_priority_queue.append(task)
        return round(self.get_queue_time() / 60, 2)

    def remove(self, task):
        if task in self.high_priority_queue:
            self.high_priority_queue.remove(task)
        if task in self.normal_priority_queue:
            self.normal_priority_queue.remove(task)
        if task in self.low_priority_queue:
            self.low_priority_queue.remove(task)

    def process(self):
        if len(self.high_priority_queue) > 0:
            return self.high_priority_queue.pop(0)
        if len(self.normal_priority_queue) > 0:
            return self.normal_priority_queue.pop(0)
        if len(self.low_priority_queue) > 0:
            return self.low_priority_queue.pop(0)
        return None

    async def start(self):
        if not self.task_finished or self.empty() :
            return
        self.task_finished = False
        task = self.process()

        # Describe the task now, while a coroutine still holds its original arguments in
        # cr_frame.f_locals; after it errors the frame (and the args) are gone. The short
        # form (name + source location) goes in the routine "Processing" log; the full
        # form (with argument values) is held back and only emitted if the task fails, to
        # keep user data out of the info-level logs.
        task_desc = describe_task(task)
        task_error_desc = describe_task(task, include_args=True)

        try:


            if not task:
                self.low_priority_queue = [i for i in self.low_priority_queue if i is not None]
                self.normal_priority_queue = [i for i in self.normal_priority_queue if i is not None]
                self.high_priority_queue = [i for i in self.high_priority_queue if i is not None]
                print(self.status())
                self.task_finished = True
                return
            if not inspect.iscoroutine(task):
                logging.info(f"Processing task: {task_desc}")
                task()
                self.task_finished = True

                print(self.status())
                return
            logging.info(f"Processing task: {task_desc}")
            if task.__name__.lower() in ["delete"]:
                await asyncio.sleep(1)
            await task

        except KeyNotFound as e:
            logging.warning(f"Key not found: {task_desc}: {e}")
        except NoPermissionException as e:
            logging.warning(f"Not enough permissions to perform task: {task_desc}: {e}")
        except discord.Forbidden as e:
            logging.warning(f"Discord Forbidden: {task_desc}: {e}")

        except discord.NotFound:
          logging.warning(f"Discord NotFound: {task_desc}")
        except Exception as e:
          logging.error(f"Error in queue while processing {task_error_desc}: {e}", exc_info=True)
        self.task_finished = True
        logging.info(self.status())



    def get_queue_time(self) -> float:
        return (len(self.high_priority_queue) + len(self.normal_priority_queue) + len(self.low_priority_queue)) * 0.3

    def get_queue_items(self) -> list :
        return self.high_priority_queue + self.normal_priority_queue + self.low_priority_queue

    def export_queue(self) -> dict :
        total = {

        }

        for i in self.high_priority_queue :
            i = i.__name__ + " (high)"
            if i in total :
                total[i] += 1
            else :
                total[i] = 1
        for i in self.normal_priority_queue :
            i = i.__name__ + " (normal)"
            if i in total :
                total[i] += 1
            else :
                total[i] = 1
        for i in self.low_priority_queue :
            i = i.__name__ + " (low)"
            if i in total :
                total[i] += 1
            else :
                total[i] = 1

        return total
