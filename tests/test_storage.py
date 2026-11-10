import json
import tempfile
import unittest
from pathlib import Path

import config
from core.actions import ClickAction, KeyAction, action_from_dict
from core.storage import (SequenceError, StateStore, default_state, load_sequence,
                          normalize_state, save_sequence)

STEPS = [ClickAction(812, 440, "Right", True), KeyAction("enter"), ClickAction(-5, 10, "Middle", False)]


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)


class StateStoreTests(TempDirCase):
    def test_missing_file_gives_defaults(self):
        store = StateStore(self.dir / "state.json")
        self.assertEqual(store.load(), default_state())

    def test_round_trip_full_state(self):
        path = self.dir / "state.json"
        state = default_state()
        state["hotkey"] = "f9"
        state["options"] = {"button": "Middle", "double": True, "freeze": True}
        state["repeat"] = {"mode": "until", "count": 7,
                           "interval": {"hours": 1, "mins": 2, "secs": 3, "ms": 400}}
        state["recording"] = {"enabled": True, "steps": [s.to_dict() for s in STEPS]}
        StateStore(path).save(state)

        loaded = StateStore(path).load()
        self.assertEqual(loaded, state)
        self.assertEqual([action_from_dict(s) for s in loaded["recording"]["steps"]], STEPS)

    def test_recording_block_only_after_selected(self):
        path = self.dir / "state.json"
        store = StateStore(path)
        state = default_state()
        state["recording"] = {"enabled": False, "steps": [KeyAction("a").to_dict()]}
        store.save(state)
        self.assertNotIn("recording", json.loads(path.read_text(encoding="utf-8")))

        state["recording"]["enabled"] = True            # selecionado
        store.save(state)
        self.assertIn("recording", json.loads(path.read_text(encoding="utf-8")))

        state["recording"]["enabled"] = False           # desmarcar não remove o bloco
        store.save(state)
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["recording"]["steps"], [KeyAction("a").to_dict()])

    def test_existing_recording_block_keeps_being_written(self):
        path = self.dir / "state.json"
        first = StateStore(path)
        state = default_state()
        state["recording"] = {"enabled": True, "steps": []}
        first.save(state)

        second = StateStore(path)                       # nova sessão
        loaded = second.load()
        loaded["recording"]["enabled"] = False
        loaded["recording"]["steps"] = [KeyAction("b").to_dict()]
        second.save(loaded)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["recording"]["steps"],
                         [KeyAction("b").to_dict()])

    def test_corrupt_file_quarantined(self):
        path = self.dir / "state.json"
        path.write_text("{ not json", encoding="utf-8")
        store = StateStore(path)
        self.assertEqual(store.load(), default_state())
        self.assertTrue((self.dir / "state.json.corrupt").exists())
        self.assertFalse(path.exists())
        self.assertIsNotNone(store.warning)

    def test_invalid_fields_fall_back(self):
        state = normalize_state({
            "hotkey": 5,
            "options": {"button": "Thumb", "double": "yes", "freeze": True},
            "repeat": {"mode": "forever", "count": -3, "interval": {"hours": "x", "ms": 250}},
            "recording": {"enabled": "maybe", "steps": [
                {"type": "click", "x": 1, "y": 2}, {"type": "boom"}, {"type": "key"}, "oops"]},
        })
        self.assertEqual(state["hotkey"], config.DEFAULT_HOTKEY)
        self.assertEqual(state["options"], {"button": "Left", "double": False, "freeze": True})
        self.assertEqual(state["repeat"]["mode"], "times")
        self.assertEqual(state["repeat"]["count"], 1)
        self.assertEqual(state["repeat"]["interval"], {"hours": 0, "mins": 0, "secs": 0, "ms": 250})
        self.assertEqual(state["recording"],
                         {"enabled": False, "steps": [ClickAction(1, 2).to_dict()]})


class SequenceFileTests(TempDirCase):
    def test_round_trip(self):
        path = str(self.dir / "seq.acseq")
        save_sequence(path, STEPS)
        self.assertEqual(load_sequence(path), STEPS)
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(raw["format"], config.SEQUENCE_FORMAT)

    def test_rejects_other_json(self):
        path = self.dir / "other.acseq"
        path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
        with self.assertRaises(SequenceError):
            load_sequence(str(path))

    def test_rejects_garbage(self):
        path = self.dir / "bad.acseq"
        path.write_text("not json at all", encoding="utf-8")
        with self.assertRaises(SequenceError):
            load_sequence(str(path))

    def test_rejects_wrong_version(self):
        path = self.dir / "v.acseq"
        path.write_text(json.dumps({"format": config.SEQUENCE_FORMAT, "version": 99, "steps": []}),
                        encoding="utf-8")
        with self.assertRaisesRegex(SequenceError, "version"):
            load_sequence(str(path))

    def test_rejects_invalid_step_with_index(self):
        path = self.dir / "s.acseq"
        payload = {"format": config.SEQUENCE_FORMAT, "version": config.SEQUENCE_VERSION,
                   "steps": [KeyAction("a").to_dict(), {"type": "click", "x": "no", "y": 1}]}
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(SequenceError, "Step 2"):
            load_sequence(str(path))

    def test_missing_file(self):
        with self.assertRaises(SequenceError):
            load_sequence(str(self.dir / "nope.acseq"))


if __name__ == "__main__":
    unittest.main()
