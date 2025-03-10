import Live
# from ableton.v2.base import task


from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.CompoundComponent import CompoundComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.Util import find_if

from .CKSpecialComponent import CKSpecialComponent
# logger = logging.getLogger(__name__)
from .StepSequencerComponent import LoopSelectorComponent
from .CKNoteEditorComponent import CKNoteEditorComponent
try:
    from itertools import imap
except ImportError:
    # Python 3...
    imap=map
from .TrackControllerComponent import TrackControllerComponent
from .Settings import Settings
from.CKUtils import *
# quantization button colours. this must remain of length 4.
QUANTIZATION_MAP = [1, 0.5, 0.25, 0.125]  # 1/4 1/8 1/16 1/32
QUANTIZATION_NAMES = ["1/4", "1/8", "1/16", "1/32"]

STEPSEQ_MODE_NORMAL = 1
STEPSEQ_MODE_MULTINOTE = 2
STEPSEQ_MODE_SCALE_EDIT = 10

LONG_BUTTON_PRESS = 1.0

class CKNoteSelectorComponent(ControlSurfaceComponent):

    def __init__(self, step_sequencer, buttons, control_surface, last_row_midi=False):
        self._clip = None
        self._step_sequencer = step_sequencer
        self._control_surface = control_surface
        ControlSurfaceComponent.__init__(self)
        self.set_enabled(False)
        self._buttons = buttons

        self._buttons[0].add_value_listener(self.note_dec_button_value)
        self._buttons[1].add_value_listener(self.note_inc_button_value)

        self._buttons[2].add_value_listener(self.velocity_dec_button_value)
        self._buttons[3].add_value_listener(self.velocity_inc_button_value)

        self._buttons[4].add_value_listener(self.shift_left_button_value)
        self._buttons[5].add_value_listener(self.shift_right_button_value)

        self._buttons[6].add_value_listener(self.random_note_button_value)
        self._buttons[7].add_value_listener(self.random_velocity_button_value)

        self._buttons[8].add_value_listener(self.half_clip_size_button_value)
        self._buttons[9].add_value_listener(self.duplicate_clip_button_value)

        self._shift_button_index = 12

        if last_row_midi:
            self._shift_button_index = 11

        self._buttons[self._shift_button_index].add_value_listener(self.shift_value_button)

        self._key = 4
        self._root_note = 36
        self._offset = 0

        self.is_drumrack = False

        self._cache = [-1, -1, -1, -1,
                       -1, -1, -1, -1,
                       -1, -1, -1, -1,
                       -1, -1, -1, -1]

    def set_selected_note(self, selected_note):
        if self.is_drumrack:
            self._root_note = int((selected_note + 12) / 16 - 1) * 16 + 4
            self._offset = (selected_note - self._root_note + 16) % 16
        else:
            self._root_note = int((selected_note - self._key) / 12) * 12 + self._key
            self._offset = (selected_note + 12 - self._root_note) % 12

    def set_enabled(self, enabled):
        ControlSurfaceComponent.set_enabled(self, enabled)


    def update(self):
        if self.is_enabled():
            for b in self._buttons:
                b.send_value(off)

            self._buttons[0].send_value(colour_amber_low)
            self._buttons[1].send_value(colour_yellow)
            self._buttons[2].send_value(colour_green_low)
            self._buttons[3].send_value(colour_green_full)
            self._buttons[4].send_value(colour_amber_low)
            self._buttons[5].send_value(colour_yellow)
            self._buttons[6].send_value(colour_red_low)
            self._buttons[7].send_value(colour_red_full)
            self._buttons[8].send_value(colour_amber_low)
            self._buttons[9].send_value(colour_yellow)
            self._buttons[self._shift_button_index].send_value(colour_red_full)


    @property
    def selected_note(self):
        return self._root_note + self._offset

    def shift_value_button(self, value):
        if value == 127:
            self._step_sequencer.shift_down()
            self._buttons[self._shift_button_index].send_value(colour_green_full)
        else:
            self._step_sequencer.shift_up()
            self._buttons[self._shift_button_index].send_value(colour_red_full)

    def note_dec_button_value(self, value):
        if value != 0:
            self._step_sequencer.decrement_note()


    def note_inc_button_value(self, value):
        if value != 0:
            self._step_sequencer.increment_note()


    def velocity_dec_button_value(self, value):
        if value != 0:
            self._step_sequencer.decrement_velocity()


    def velocity_inc_button_value(self, value):
        if value != 0:
            self._step_sequencer.increment_velocity()

    def shift_left_button_value(self, v):
        if v != 0:
            self._step_sequencer.shift_clip_notes_left()

    def shift_right_button_value(self, v):
        if v != 0:
            self._step_sequencer.shift_clip_notes_right()

    def random_note_button_value(self, v):
        if v != 0:
            self._step_sequencer.randomise_notes()


    def random_velocity_button_value(self, v):
        if v != 0:
            self._step_sequencer.randomise_velocities()

    def half_clip_size_button_value(self, v):
        if v != 0:
            self._step_sequencer.half_clip_size()

    def duplicate_clip_button_value(self, v):
        if v != 0:
            self._step_sequencer.double_or_duplicate_clip()

    def set_clip(self, clip):
        self._clip = clip

    def set_note_cache(self, note_cache):
        pass



class CKStepSequencerComponent(CompoundComponent):

    def __init__(self, matrix, side_buttons, top_buttons, control_surface, last_row_midi):
        self._osd = None
        self._control_surface = control_surface
        self._number_of_lines_per_note = 1
        super(CKStepSequencerComponent, self).__init__()
        self.QUANTIZATION_COLOR_MAP = ["StepSequencer.Quantization.One", "StepSequencer.Quantization.Two", "StepSequencer.Quantization.Three", "StepSequencer.Quantization.Four"]
        self.QUANTIZATION_COLOR_MAP_LOW = ["StepSequencer.QuantizationLow.One", "StepSequencer.QuantizationLow.Two", "StepSequencer.QuantizationLow.Three", "StepSequencer.QuantizationLow.Four"]
        self._name = "drum step sequencer"
        # clip
        self._clip = None
        self._clip_slot = None
        self._playhead = 0
        self._new_clip_pages = 4
        # mode
        self._mode = STEPSEQ_MODE_NORMAL
        self._mode_backup = self._mode
        # buttons
        self._height = matrix.height()
        self._width = matrix.width()
        self._matrix = matrix
        self._top_buttons = top_buttons
        self._side_buttons = side_buttons
        self._left_button = None
        self._right_button = None
        # scale
        self._root_note = 36
        self._chromatic_scale = []
        self._diatonic_scale = []

        self._quantization_index = 2 # keep new clip creation happy
        self._quantization = 0.25
        self._beat = 0

        # new
        self._selected_track = None
        self._last_row_midi = last_row_midi

        # setup
        self._set_loop_selector()
        self._set_note_editor()
        self._set_note_selector()
        self._set_track_controller()
        self._set_special()
        self._scale_updated()


        #legacy
        self._is_mute_shifted = False

        self.set_scene_triggers()
        # TODO: maybe clean this... this should be done on enable.
        # self.on_clip_slot_changed()

    def set_scene_triggers(self):
        for b in self._side_buttons:
            b.add_value_listener(self.on_scene_trigger, identify_sender=True)
            b.send_value(colour_amber_low)

    def on_scene_trigger(self, value, sender):
        if value != 0:
            for b in self._side_buttons:
                b.send_value(colour_amber_low)

            idx = int((sender.identifier / 8) / 2)
            self.song().scenes[idx].fire()
            self._side_buttons[idx].send_value(colour_green_full)

    def disconnect(self):
        self._clip = None

        self._shift_button = None
        self._top_buttons = None
        self._side_buttons = None
        self._matrix = None

        self._loop_selector = None
        self._note_editor = None
        self._note_selector = None
        self._track_controller = None


    # Set 4x4 lower right matrix section that manages the loop range OK
    def _set_loop_selector(self):
        self._loop_selector = self.register_component(LoopSelectorComponent(self, [
            self._matrix.get_button(4, 4), self._matrix.get_button(5, 4), self._matrix.get_button(6, 4), self._matrix.get_button(7, 4),
            self._matrix.get_button(4, 5), self._matrix.get_button(5, 5), self._matrix.get_button(6, 5), self._matrix.get_button(7, 5)],
            # self._matrix.get_button(4, 6), self._matrix.get_button(5, 6), self._matrix.get_button(6, 6), self._matrix.get_button(7, 6),
            # self._matrix.get_button(4, 7), self._matrix.get_button(5, 7), self._matrix.get_button(6, 7), self._matrix.get_button(7, 7),
                                                                            self._control_surface)
                                                      )

    def _set_special(self):

        buttons = [
            self._matrix.get_button(4, 6),
            self._matrix.get_button(5, 6),
            self._matrix.get_button(6, 6),
            self._matrix.get_button(7, 6)]

        self._special_component = self.register_component(
            CKSpecialComponent(self, buttons, self._control_surface, self._last_row_midi))

    #Allow to manipulate the LP grid and Live's Clip notes (add/del, velocity, mute, etc)
    #In charge of refreshing the notes LED matrix
    #Display page indicator for multinote mode
    def _set_note_editor(self):
        self._note_editor = self.register_component(CKNoteEditorComponent(self, self._matrix, self._control_surface))
        # self._note_editor.set_velocity_button(self._side_buttons[6])#Solo

    #Set 4x4 lower left matrix section that allows note selection in Normal Mode
    def _set_note_selector(self):
        # self._note_selector.set_up_button(self._side_buttons[4])#Stop
        # self._note_selector.set_down_button(self._side_buttons[5])#Trk On

        pads = [
            self._matrix.get_button(0, 4), self._matrix.get_button(1, 4), self._matrix.get_button(2, 4), self._matrix.get_button(3, 4),
            self._matrix.get_button(0, 5), self._matrix.get_button(1, 5), self._matrix.get_button(2, 5), self._matrix.get_button(3, 5),
            self._matrix.get_button(0, 6), self._matrix.get_button(1, 6), self._matrix.get_button(2, 6), self._matrix.get_button(3, 6),
        ]

        if not self._last_row_midi:
            pads.extend([self._matrix.get_button(0, 7), self._matrix.get_button(1, 7), self._matrix.get_button(2, 7), self._matrix.get_button(3, 7)])

        self._note_selector = self.register_component(CKNoteSelectorComponent(self, pads, self._control_surface, self._last_row_midi))

    def _set_track_controller(self):#Navigation buttons
        self._track_controller = self.register_component(TrackControllerComponent(self._control_surface, implicit_arm = False))
        self._track_controller.set_enabled(False)
        self._track_controller.set_prev_scene_button(self._top_buttons[0])
        self._track_controller.set_next_scene_button(self._top_buttons[1])
        self._track_controller.set_prev_track_button(self._top_buttons[2])
        self._track_controller.set_next_track_button(self._top_buttons[3])


    def set_osd(self, osd):
        self._osd = osd

    def _update_OSD(self):
        if self._osd != None:
            if self._mode == STEPSEQ_MODE_MULTINOTE:
                self._osd.set_mode('Drum Step Sequencer (multinote)')
            else:
                self._osd.set_mode('Drum Step Sequencer')

            if self._clip != None:
                self._osd.attributes[0] = " "
                self._osd.attribute_names[0] = " "
                self._osd.attributes[1] = " "
                self._osd.attribute_names[1] = " "
                self._osd.attributes[2] = " "
                self._osd.attribute_names[2] = " "
                self._osd.attributes[3] = " "
                self._osd.attribute_names[3] = " "
                self._osd.attributes[4] = " "
                self._osd.attribute_names[4] = " "
                self._osd.attributes[5] = " "
                self._osd.attribute_names[5] = " "
                self._osd.attributes[6] = " "
                self._osd.attribute_names[6] = " "
                self._osd.attributes[7] = " "
                self._osd.attribute_names[7] = " "
            else:
                self._osd.attributes[0] = " "
                self._osd.attribute_names[0] = " "
                self._osd.attributes[1] = " "
                self._osd.attribute_names[1] = " "
                self._osd.attributes[2] = " "
                self._osd.attribute_names[2] = " "
                self._osd.attributes[3] = " "
                self._osd.attribute_names[3] = " "
                self._osd.attributes[4] = " "
                self._osd.attribute_names[4] = " "
                self._osd.attributes[5] = " "
                self._osd.attribute_names[5] = " "
                self._osd.attributes[6] = " "
                self._osd.attribute_names[6] = " "
                self._osd.attributes[7] = " "
                self._osd.attribute_names[7] = " "

            if self._selected_track != None:
                self._osd.info[0] = "track : " + self._selected_track.name
            else:
                self._osd.info[0] = " "
            if self._clip != None:
                name = self._clip.name
                if name == "":
                    name = "(unamed clip)"

                self._osd.info[1] = "clip : " + name
            else:
                self._osd.info[1] = "no clip selected"
            self._osd.update()

    @property
    def _is_velocity_shifted(self):
        return self._note_editor._is_velocity_shifted

    def index_of(self, pad_list, pad):
        for i in range(0, len(pad_list)):
            if (pad_list[i] == pad):
                return i
        return(-1)

    # enabled
    def set_enabled(self, enabled):
        if enabled:
            if self._mode == STEPSEQ_MODE_SCALE_EDIT:
                self.set_mode(self._mode_backup)
            # clear note editor cache
            self._note_editor._force_update = True

            # todo: find a better way to init?
            if self._mode == -1:
                self._mode = STEPSEQ_MODE_NORMAL
                self._detect_scale_mode()

            # sync to selected pad
            self._update_drum_group_device()
            if(self._drum_group_device): #Select the note
                self._note_selector.set_selected_note(self.index_of(self._drum_group_device.drum_pads,self._drum_group_device.view.selected_drum_pad)) #FIX set view again
                self._ck_note_selector.set_selected_note(self.index_of(self._drum_group_device.drum_pads,self._drum_group_device.view.selected_drum_pad)) #FIX set view again

            self._track_controller.set_enabled(enabled)
            self._note_editor.set_enabled(enabled)
            # update clip notes as they might have changed while we were sleeping
            self.on_clip_slot_changed()
            # call super.set_enabled()
            CompoundComponent.set_enabled(self, enabled)

            self._on_notes_changed()
            self._update_OSD()

        else:
            self._track_controller.set_enabled(enabled)
            self._loop_selector.set_enabled(enabled)
            self._note_selector.set_enabled(enabled)
            self._note_editor.set_enabled(enabled)
            CompoundComponent.set_enabled(self, enabled)

    def set_mode(self, mode, number_of_lines_per_note=1):
        if self._mode != mode or number_of_lines_per_note != self._number_of_lines_per_note:
            self._number_of_lines_per_note = number_of_lines_per_note
            self._note_editor.set_multinote(mode == STEPSEQ_MODE_MULTINOTE, number_of_lines_per_note)
            if mode == STEPSEQ_MODE_NORMAL:
                if self._mode != mode:
                    self._note_editor.set_page(self._loop_selector._block)
                self.set_left_button(None)
                self.set_right_button(None)
                self._track_controller.set_prev_track_button(self._top_buttons[2])
                self._track_controller.set_next_track_button(self._top_buttons[3])
            else:
                if self._mode != mode:
                    self._note_editor.set_page(self._loop_selector._block)
                self._track_controller.set_prev_track_button(None)
                self._track_controller.set_next_track_button(None)
                self.set_left_button(self._top_buttons[2])
                self.set_right_button(self._top_buttons[3])
            self._mode = mode
            self._note_editor._force_update = True
            self.update()

    def set_page(self, block):
        self._note_editor.set_page(block)
        self._note_editor.update()

    # SCALE
    def _scale_updated(self):
        self._control_surface.log_message("scale updated")
        keys = [0, 0, 0, 0, 0, 0, 0, 0]
        key_is_root_note = [False, False, False, False, False, False, False, False]
        key_is_in_scale = [False, False, False, False, False, False, False, False]
        # if self._note_selector.is_drumrack:
        #     for i in range(8):
        #         keys[i] = self._note_selector.selected_note + i
        #         key_is_root_note[i] = (keys[i] + 12 + 16) % 16 == 0
        #         key_is_in_scale[i] = (keys[i] + 12 + 16) % 4 == 0
        # elif self._note_selector.is_diatonic:
        #     self._note_selector._scale_length = len(self._note_selector._scale)
        #     try:
        #         idx = self._note_selector._scale.index(self._note_selector._offset)
        #     except ValueError:
        #         idx = -1
        #     if(idx == -1):
        #         self._control_surface.log_message("not found : " + str(self._note_selector._offset) + " in " + str(self._note_selector._scale))
        #         for i in range(8):
        #             keys[i] = self._note_selector._root_note + self._note_selector._offset + i
        #     else:
        #         for i in range(8):
        #             keys[i] = self._note_selector._root_note + self._note_selector._scale[(i + idx) % self._note_selector._scale_length] + int((i + idx) / self._note_selector._scale_length) * 12
        #             key_is_root_note[i] = (keys[i] + 12) % 12 == self._note_selector._key
        #             key_is_in_scale[i] = True
        # else:
        #     for i in range(8):
        #         keys[i] = self._note_selector.selected_note + i
        #         key_is_root_note[i] = (keys[i] + 12) % 12 == self._note_selector._key
        #         key_is_in_scale[i] = (keys[i] - self._note_selector._key + 12) % 12 in self._note_selector._scale
        #

        for i in range(8):
            keys[i] = self._note_selector.selected_note + i
            key_is_root_note[i] = (keys[i] + 12) % 12 == self._note_selector._key
            key_is_in_scale[i] = True #(keys[i] - self._note_selector._key + 12) % 12 in self._note_selector._scale



        self._note_editor.set_key_indexes(keys)
        self._note_editor.set_key_index_is_in_scale(key_is_in_scale)
        self._note_editor.set_key_index_is_root_note(key_is_root_note)
        self._update_note_editor()
        self._update_note_selector()

    def increment_note(self):
        self._note_editor.increment_selected_note()
        self.update()

    def shift_down(self):
        self._note_editor.shift_down()
    def shift_up(self):
        self._note_editor.shift_up()

    def decrement_note(self):
        self._note_editor.decrement_selected_note()
        self.update()

    def increment_velocity(self):
        self._note_editor.increment_selected_note_velocity()
        self.update()

    def decrement_velocity(self):
        self._note_editor.decrement_selected_note_velocity()
        self.update()

    def shift_clip_notes_left(self):
        self._note_editor.shift_clip_notes_left()

    def shift_clip_notes_right(self):
        self._note_editor.shift_clip_notes_right()


    def randomise_notes(self):
        self._note_editor.randomise_notes()

    def randomise_velocities(self):
        self._note_editor.randomise_velocities()

    def half_clip_size(self):
        self._note_editor.half_clip_size()

    def double_or_duplicate_clip(self):
        self._note_editor.double_or_duplicate_clip()

    # UPDATE
    def update(self):
        if self.is_enabled():
            self._update_track_controller()
            self._update_loop_selector()
            self._update_note_selector()
            self._update_buttons()
            self._update_note_editor()
            self._update_OSD()
            # show clip !
            # if not self._is_locked and self._clip != None:
            #     if ((not self.application().view.is_view_visible('Detail')) or (not self.application().view.is_view_visible('Detail/Clip'))):
            #         self.application().view.show_view('Detail')
            #         self._control_surface.log_message(f"CKSeq update siwtching to Detail/Clip line 554")
            #         self.application().view.show_view('Detail/Clip')

    def _update_track_controller(self):
        if self._track_controller != None:
            self._track_controller.set_enabled(True)

    def _update_loop_selector(self):
        self._loop_selector.set_enabled(self._mode == STEPSEQ_MODE_NORMAL)
        self._loop_selector.update()

    def _update_note_selector(self):
        # pass
        # self._note_selector._enable_offset_button = self._mode == STEPSEQ_MODE_NORMAL
        self._note_selector.set_enabled(self._mode != STEPSEQ_MODE_SCALE_EDIT)
        self._note_selector.update()

    def note_editor_height(self):
        midi_row_offset = 1 if self._last_row_midi else 0
        return self._height - (4 - midi_row_offset)

    def _update_note_editor(self):
        # self._control_surface.log_message(f"self._mode = {self._mode}")
        # self._control_surface.log_message(f"self._height = {self._height}")
        # self._control_surface.log_message(f"self._mode = {self._mode == STEPSEQ_MODE_NORMAL}")
        self._note_editor.set_multinote(self._mode == STEPSEQ_MODE_MULTINOTE, self._number_of_lines_per_note)
        if self._mode == STEPSEQ_MODE_NORMAL:
            self._note_editor.set_height(self.note_editor_height())
        else:
            self._note_editor.set_height(self.note_editor_height())
        self._note_editor.set_enabled(self._mode != STEPSEQ_MODE_SCALE_EDIT)
        self._note_editor.update()

    def _update_buttons(self):
        self._update_left_button()
        self._update_right_button()


    # CLIP CALLBACKS
    def on_track_list_changed(self):
        self.on_selected_track_changed()

    def on_scene_list_changed(self):
        self.on_selected_scene_changed()

    def on_selected_scene_changed(self):
        self.on_clip_slot_changed()
        self.update()

    def on_selected_track_changed(self):
        self._control_surface.log_message(f"on_selected_track_changed self = {self}")
        self._detect_scale_mode()
        self.on_clip_slot_changed()
        self.update()

    def _on_loop_changed(self):
        if self.is_enabled() and self._clip != None:
            self._loop_selector._get_clip_loop()

    def on_clip_slot_has_clip_changed(self):
        # the clip was deleted. unlock.
        self.on_clip_slot_changed()
        self.update()

    def on_clip_slot_changed(self, scheduled=False):
        # get old reference to clipslot
        clip_slot = self._clip_slot

        # update track if not track locked
        self._selected_track = self.song().view.selected_track

        # update scene
        if self._selected_track != None:
            idx = -1

            # unlocked mode
            try:
                idx = list(self.song().scenes).index(self.song().view.selected_scene)
            except ValueError:
                idx = -1
            if(idx != -1 and idx < len(list(self._selected_track.clip_slots))):
                clip_slot = self._selected_track.clip_slots[idx]

        # update clip slot
        if clip_slot != self._clip_slot or self._clip_slot == None:
            if clip_slot != None and clip_slot.has_clip_has_listener(self.on_clip_slot_has_clip_changed):
                clip_slot.remove_has_clip_listener(self.on_clip_slot_has_clip_changed)
            self._clip_slot = clip_slot
            if self._clip_slot != None:
                if self._clip_slot.has_clip_has_listener(self.on_clip_slot_has_clip_changed):
                    self._clip_slot.remove_has_clip_listener(self.on_clip_slot_has_clip_changed)
                self._clip_slot.add_has_clip_listener(self.on_clip_slot_has_clip_changed)

        if self._clip_slot != None and self._clip_slot.has_clip and self._clip_slot.clip != None and self._clip_slot.clip.is_midi_clip:
            if self._clip == None or self._clip != self._clip_slot.clip:
                # unlink
                if self._clip != None and self._clip.is_midi_clip:
                    if self._clip.notes_has_listener(self._on_notes_changed):
                        self._clip.remove_notes_listener(self._on_notes_changed)
                    if self._clip.playing_status_has_listener(self._on_playing_status_changed):
                        self._clip.remove_playing_status_listener(self._on_playing_status_changed)
                    if self._clip.playing_position_has_listener(self._on_playing_position_changed):
                        self._clip.remove_playing_position_listener(self._on_playing_position_changed)
                    if self._clip.loop_start_has_listener(self._on_loop_changed):
                        self._clip.remove_loop_start_listener(self._on_loop_changed)
                    if self._clip.loop_end_has_listener(self._on_loop_changed):
                        self._clip.remove_loop_end_listener(self._on_loop_changed)

                #load scale settings from clip
                if Settings.STEPSEQ__SAVE_SCALE != None and Settings.STEPSEQ__SAVE_SCALE == "clip":
                    #must set clip to None otherwise it trigger a clip note update which we dont want.
                    self._clip = None
                    self._note_editor._clip_slot = None

                # link new clip
                self._clip_slot.clip.add_notes_listener(self._on_notes_changed)
                self._clip_slot.clip.add_playing_status_listener(self._on_playing_status_changed)
                self._clip_slot.clip.add_playing_position_listener(self._on_playing_position_changed)
                self._clip_slot.clip.add_loop_start_listener(self._on_loop_changed)
                self._clip_slot.clip.add_loop_end_listener(self._on_loop_changed)

                # publish
                self._clip = self._clip_slot.clip

                # update
                #if scheduled:
                self._clip_changed()
                #else:
                #self._control_surface.schedule_message(1, self._clip_changed)
            else:
                # same clip...
                pass

        else:
            # unlink
            if self._clip != None:
                if self._clip.notes_has_listener(self._on_notes_changed):
                    self._clip.remove_notes_listener(self._on_notes_changed)
                if self._clip.playing_status_has_listener(self._on_playing_status_changed):
                    self._clip.remove_playing_status_listener(self._on_playing_status_changed)
                if self._clip.playing_position_has_listener(self._on_playing_position_changed):
                    self._clip.remove_playing_position_listener(self._on_playing_position_changed)
                if self._clip.loop_start_has_listener(self._on_loop_changed):
                    self._clip.remove_loop_start_listener(self._on_loop_changed)
                if self._clip.loop_end_has_listener(self._on_loop_changed):
                    self._clip.remove_loop_end_listener(self._on_loop_changed)

            # publish
            self._clip = None
            self._clip_changed()

    def _clip_changed(self):  # triggered by _on_clip_slot_changed() or manually on enable.
        self._control_surface.log_message(f"_clip_changed self._clip_changed = {self._clip_slot}")
        self._note_editor.set_clip(self._clip)
        self._note_selector.set_clip(self._clip)
        self._loop_selector.set_clip(self._clip)
        self._special_component.set_clip_slot(self._clip_slot)
        self._note_editor.set_playhead(None)
        # self._note_selector.set_playhead(None)
        self._loop_selector.set_playhead(None)
        # reload notes
        self._on_notes_changed()

    def _on_notes_changed(self):  # trigger by callback on clip or via _clip_changed.
        pass

    # PLAY POSITION
    def _on_playing_status_changed(self):  # playing status changed listener
        if self.is_enabled():
            self._on_playing_position_changed()

    def _on_playing_position_changed(self):  # playing position changed listener
        if self.is_enabled():
            if self._clip != None and self._clip.is_playing and self.song().is_playing:
                self._playhead = self._clip.playing_position
            else:
                self._playhead = None
            self._loop_selector.set_playhead(self._playhead)
            # self._note_selector.set_playhead(self._playhead)
            self._note_editor.set_playhead(self._playhead)

    # DRUM_GROUP_DEVICE
    def _update_drum_group_device(self):
        if self.song().view.selected_track != None:
            track = self.song().view.selected_track
            if(track.devices != None and len(track.devices) > 0):
                #device = track.devices[0]
                device = self.find_drum_group_device(track)
                if(device!= None and device.can_have_drum_pads and device.has_drum_pads):#Is drumrack and it have pads
                    self._drum_group_device = device
                else:
                    self._drum_group_device = None
            else:
                self._drum_group_device = None
        else:
            self._drum_group_device = None

    def _detect_scale_mode(self):

        self._update_drum_group_device()

    def find_drum_group_device(self, track):
        device = find_if(lambda d: d.type == Live.Device.DeviceType.instrument, track.devices)#find track's Instrument device
        if device:
            if device.can_have_drum_pads:#device is a drum rack??
                return device
            elif device.can_have_chains:#device is a rack??
                return find_if(bool, imap(self.find_drum_group_device, device.chains))#recursive->returns the first drum rack item of the chain
        else:
            return None

    def _update_right_button(self):
        if self.is_enabled():
            if self._right_button != None:
                if self._clip != None:
                    self._right_button.set_on_off_values("DefaultButton")
                    if self._loop_selector.can_scroll(1):
                        self._right_button.turn_on()
                    else:
                        self._right_button.turn_off()
                else:
                    self._right_button.set_light("DefaultButton.Disabled")

    def set_right_button(self, button):
        assert (isinstance(button, (ButtonElement, type(None))))
        if (button != self._right_button):
            if (self._right_button != None):
                self._right_button.remove_value_listener(self._right_value)
            self._right_button = button
            if (self._right_button != None):
                self._right_button.add_value_listener(self._right_value, identify_sender=True)

    def _right_value(self, value, sender):
        assert (self._right_button != None)
        assert (value in range(128))
        if self.is_enabled() and self._clip != None:
            if ((value is not 0) or (not sender.is_momentary())):
                self._loop_selector.scroll(1)
                self._note_editor.request_display_page()
                self.update()

    # LEFT Button
    def _update_left_button(self):
        if self.is_enabled():
            if self._left_button != None:
                if self._clip != None:
                    self._left_button.set_on_off_values("DefaultButton")
                    if self._loop_selector.can_scroll(-1):
                        self._left_button.turn_on()
                    else:
                        self._left_button.turn_off()
                else:
                    self._left_button.set_light("DefaultButton.Disabled")

    def set_left_button(self, button):
        assert (isinstance(button, (ButtonElement, type(None))))
        if (button != self._left_button):
            if (self._left_button != None):
                self._left_button.remove_value_listener(self._left_value)
            self._left_button = button
            if (self._left_button != None):
                self._left_button.add_value_listener(self._left_value, identify_sender=True)

    def _left_value(self, value, sender):
        assert (self._right_button != None)
        assert (value in range(128))
        if self.is_enabled() and self._clip != None:
            if ((value is not 0) or (not sender.is_momentary())):
                self._loop_selector.scroll(-1)
                self._note_editor.request_display_page()
                self.update()

    # UTILS
    def create_clip(self):
        if self.song().view.highlighted_clip_slot != None:
            clip_slot = self.song().view.highlighted_clip_slot
            if not clip_slot.has_clip:
                if self._mode == STEPSEQ_MODE_NORMAL:
                    clip_slot.create_clip(QUANTIZATION_MAP[self._quantization_index] * 8 * 4)
                else:
                    clip_slot.create_clip(QUANTIZATION_MAP[self._quantization_index] * 8)
                self._detect_scale_mode()
                clip_slot.fire()
                self.on_clip_slot_changed()
                self.update()

    def duplicate_clip(self):
        if self._clip_slot and self._clip_slot.has_clip:
            try:
                track = self._clip_slot.canonical_parent
                newIdx = track.duplicate_clip_slot(list(track.clip_slots).index(self._clip_slot))
                self.song().view.selected_scene = self.song().scenes[newIdx]
                #if track.clip_slots[newIdx] != None:
                #track.clip_slots[newIdx].fire()
                self.on_clip_slot_changed()
                self.update()
            except Live.Base.LimitationError:
                pass
            except RuntimeError:
                pass
