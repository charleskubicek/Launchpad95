import Live
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
        self._buttons[1].add_value_listener(self.bounce_in_place_button_value)
        self._buttons[1].send_value(colour_red_full)
        self._buttons[2].add_value_listener(self.audio_to_simpler_value)
        self._buttons[2].send_value(colour_red_full)
        self._buttons[3].add_value_listener(self.record_midi_automation_button_value)
        self._buttons[3].send_value(colour_red_full)

    def set_clip_slot(self, clip_slot):
        self._clip_slot = clip_slot

    def record_midi_automation_button_value(self, v):
        if v != 0:
            self.record_midi_automation()

    def rec_record_midi_automation(self, v):
        if v != 0:
            self._tasks.add(Task.sequence(Task.delay(1), Task.run(self.record_midi_automation)))

    def record_midi_automation(self):
        self.song().session_automation_record = True
        self.song().record_mode = 1

    def rec_midi_button_value(self, v):
        self._control_surface.log_message(f"rec_midi_button_value v = {v}")
        if v != 0:
            self._tasks.add(Task.sequence(Task.delay(1), Task.run(self.record_midi_notes)))

    def bounce_in_place_button_value(self, v):
        self._control_surface.log_message(f"bounce_in_place_button_value v = {v}")
        if v != 0:
            self._tasks.add(Task.sequence(Task.delay(1), Task.run(self.bounce_in_place)))

    def audio_to_simpler_value(self, v):
        if v != 0:
            self._tasks.add(Task.sequence(Task.delay(1), Task.run(self.audio_to_simpler)))

    def delete_extra_default_devices(self, new_track):
        total_devices = len(new_track.devices)
        device_deletions = int((total_devices - 1) / 2)

        for i in range(0, device_deletions):
            self._control_surface.log_message(
                f" deleting device at index: {len(new_track.devices) - 1}: {new_track.devices[len(new_track.devices) - 1].name}")
            new_track.delete_device(len(new_track.devices) - 1)

    def audio_to_simpler(self):
        original_track = self.song().view.selected_track

        if original_track.has_midi_input:
            self._control_surface.show_message("Current track isn't an audio track")
            return

        song = self.song()
        # get clip from arrangement
        clip = self.song().view.highlighted_clip_slot.clip

        Live.Conversions.create_midi_track_with_simpler(song, clip)
        new_track = self.song().view.selected_track

        self._control_surface.log_message(f"original track naame: {original_track.name}")
        self._control_surface.log_message(f"     new track naame: {new_track.name}")
        new_track.name = new_track.name + ' ' + original_track.name

        self.delete_extra_default_devices(new_track)

    def bounce_in_place(self):
        current_track = self.song().view.selected_track
        idx = list(self.song().scenes).index(self.song().view.selected_scene)
    
        new_track = self.song().create_audio_track()
    
        for i in new_track.available_input_routing_types:
            if i.display_name == current_track.name:
                new_track.current_monitoring_state = 0
                new_track.input_routing_type = i
                new_track.arm = 1
                break
        else:
            self._constrol_surface.show_message("Couldn't configure Routing")

        new_track.name = f"[Audio from {current_track.name}]"
        self.song().is_playing = False

        self._control_surface.log_message(f"bounce_in_place self._clip_slot = {self._clip_slot}")
        if self._clip_slot is not None and idx != -1 and idx < len(list(new_track.clip_slots)):
            new_clip_slot = new_track.clip_slots[idx]
            self._tasks.add(Task.sequence(Task.delay(10), Task.run(new_clip_slot.fire)))
            self.application().view.show_view('Detail')
            self.application().view.show_view('Detail/Clip')
            self._constrol_surface.show_message("Recording Audio")
        else:
            self._constrol_surface.show_message("Failed to record Audio")


    def record_midi_notes(self):

        current_track = self.song().view.selected_track
        idx = list(self.song().scenes).index(self.song().view.selected_scene)

        if not current_track.has_midi_input:
            self._constrol_surface.show_message("Current track isn't a midi track")
            return

        new_track = self.song().create_midi_track()

        for i in new_track.available_input_routing_types:
            if i.display_name == current_track.name:
                new_track.current_monitoring_state = 0
                new_track.input_routing_type = i
                new_track.arm = 1
                break
        else:
            self._constrol_surface.show_message("Couldn't configure Routing")

        new_track.name = f"[Midi from {current_track.name}]"
        self.song().is_playing = False

        self._control_surface.log_message(f"record_midi_notes self._clip_slot = {self._clip_slot}")
        if self._clip_slot is not None and idx != -1 and idx < len(list(new_track.clip_slots)):
            new_clip_slot = new_track.clip_slots[idx]
            self._tasks.add(Task.sequence(Task.delay(10), Task.run(new_clip_slot.fire)))
            self.application().view.show_view('Detail')
            self.application().view.show_view('Detail/Clip')
            self._constrol_surface.show_message("Recording MIDI")
        else:
            self._constrol_surface.show_message("Failed to record MIDI")