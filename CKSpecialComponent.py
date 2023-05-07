from _Framework import Task
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent

from.CKUtils import *


class CKSpecialComponent(ControlSurfaceComponent):

    def __init__(self, step_sequencer, buttons, control_surface, last_row_midi=False):
        ControlSurfaceComponent.__init__(self)
        self._last_row_midi = last_row_midi
        self._control_surface = control_surface
        self._buttons = buttons
        self._step_sequencer = step_sequencer
        self._clip_slot = None

        self._control_surface.log_message(f"__init__ self = {self}")

        self._buttons[0].add_value_listener(self.rec_midi_button_value)
        self._buttons[0].send_value(colour_red_full)

    def set_clip_slot(self, clip_slot):
        self._clip_slot = clip_slot

    def rec_midi_button_value(self, v):
        self._control_surface.log_message(f"rec_midi_button_value v = {v}")
        if v != 0:
            self._tasks.add(Task.sequence(Task.delay(1), Task.run(self.record_midi_notes)))

    def record_midi_notes(self):

        current_track = self.song().view.selected_track
        idx = list(self.song().scenes).index(self.song().view.selected_scene)

        if not current_track.has_midi_input:
            self.show_message("Current track isn't a midi track")
            return

        new_track = self.song().create_midi_track()

        for i in new_track.available_input_routing_types:
            if i.display_name == current_track.name:
                new_track.current_monitoring_state = 0
                new_track.input_routing_type = i
                new_track.arm = 1
                break
        else:
            self.show_message("Couldn't configure Routing")

        new_track.name = f"[Midi from {current_track.name}]"
        self.song().is_playing = False

        self._control_surface.log_message(f"record_midi_notes self._clip_slot = {self._clip_slot}")
        if self._clip_slot is not None and idx != -1 and idx < len(list(new_track.clip_slots)):
            new_clip_slot = new_track.clip_slots[idx]
            self._tasks.add(Task.sequence(Task.delay(10), Task.run(new_clip_slot.fire)))
            self.application().view.show_view('Detail')
            self.application().view.show_view('Detail/Clip')
            self.show_message("Recording MIDI")
        else:
            self.show_message("Failed to record MIDI")