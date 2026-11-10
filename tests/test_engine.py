import threading
import time
import unittest

from core.actions import ClickAction, KeyAction
from core.engine import ClickEngine, ClickerConfig


class FakeBackend:
    def __init__(self, start=(100, 100)):
        self.pos = start
        self.events = []

    @property
    def position(self):
        return self.pos

    def move(self, x, y):
        self.pos = (x, y)
        self.events.append(("move", x, y))

    def click(self, button, double=False):
        self.events.append(("click", button, double, self.pos))

    def press_key(self, name):
        self.events.append(("key", name))


def run(cfg, backend=None, timeout=5):
    backend = backend or FakeBackend()
    done = threading.Event()
    result = {}

    def finished(err):
        result["err"] = err
        done.set()

    engine = ClickEngine(backend, on_finish=finished)
    engine.start(cfg)
    assert done.wait(timeout), "engine did not finish"
    return engine, backend, result["err"]


class EngineTests(unittest.TestCase):
    def test_simple_repeat_n(self):
        engine, backend, err = run(ClickerConfig(button="Right", double=True, repeat_count=5, interval=0.001))
        self.assertIsNone(err)
        clicks = [e for e in backend.events if e[0] == "click"]
        self.assertEqual(len(clicks), 5)
        self.assertEqual(clicks[0][1:3], ("Right", True))
        self.assertEqual(engine.count, 5)

    def test_interval_respected(self):
        t0 = time.monotonic()
        run(ClickerConfig(repeat_count=4, interval=0.05))
        self.assertGreaterEqual(time.monotonic() - t0, 0.14)   # 3 esperas de 50 ms

    def test_recording_order_and_repeat(self):
        steps = [ClickAction(10, 20, "Left"), KeyAction("enter"), ClickAction(30, 40, "Middle", True)]
        _, backend, _ = run(ClickerConfig(repeat_count=2, interval=0.001, steps=steps))
        kinds = [e[0] for e in backend.events if e[0] in ("click", "key")]
        self.assertEqual(kinds, ["click", "key", "click"] * 2)
        self.assertEqual(backend.events[0], ("move", 10, 20))

    def test_until_stopped_and_stop_is_fast(self):
        backend = FakeBackend()
        engine = ClickEngine(backend)
        engine.start(ClickerConfig(repeat_count=None, interval=30))   # long wait
        time.sleep(0.1)
        t0 = time.monotonic()
        engine.stop()
        engine.join(2)
        self.assertFalse(engine.running)
        self.assertLess(time.monotonic() - t0, 0.5)
        self.assertEqual(engine.count, 1)

    def test_freeze_restores_pointer(self):
        backend = FakeBackend((50, 60))
        engine = ClickEngine(backend)
        engine.start(ClickerConfig(repeat_count=None, interval=0.2, freeze=True))
        time.sleep(0.05)
        backend.pos = (500, 500)                 # user drags the mouse
        time.sleep(0.1)
        self.assertEqual(backend.pos, (50, 60))
        engine.stop()
        engine.join(2)

    def test_freeze_off_does_not_move(self):
        backend = FakeBackend((50, 60))
        run(ClickerConfig(repeat_count=3, interval=0.001), backend)
        self.assertFalse([e for e in backend.events if e[0] == "move"])

    def test_backend_error_reported(self):
        class Boom(FakeBackend):
            def click(self, *args, **kwargs):
                raise RuntimeError("boom")

        _, _, err = run(ClickerConfig(repeat_count=1), Boom())
        self.assertEqual(err, "boom")


if __name__ == "__main__":
    unittest.main()
