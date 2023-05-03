from dataclasses import dataclass
from random import randrange

from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement
import time
import Live

# Single notes only!
class CKNoteEditorComponent(ControlSurfaceComponent):

    def __init__(self, stepsequencer=None, matrix=None, control_surface=None):
        ControlSurfaceComponent.__init__(self)
        self._stepsequencer = stepsequencer
        self._control_surface = control_surface
        self.set_enabled(False)
        self._clip = None
        # self._note_cache = None
        self._playhead = None
        self._shift_down = False

        # buttons
        self._matrix = None

        # playback step indicator
        self.display_metronome = True
        self.metronome_color = "StepSequencer.NoteEditor.Metronome"

        self._quantization = 0.25

        # clip
        self._force_update = True

        # other colors
        self.muted_note_color = "StepSequencer.NoteEditor.Muted"
        self.playing_note_color = "StepSequencer.NoteEditor.Playing"

        # displayed page
        self._page = 0
        self._display_page = False
        self._display_page_time = time.time()

        # modes
        self._is_mute_shifted = False

        # Velocity color map. this must remain of length 3. WHY???
        self.velocity_map = [20, 50, 80, 105, 127]
        self.velocity_color_map = ["StepSequencer.NoteEditor.Velocity0", "StepSequencer.NoteEditor.Velocity1",
                                   "StepSequencer.NoteEditor.Velocity2", "StepSequencer.NoteEditor.Velocity3",
                                   "StepSequencer.NoteEditor.Velocity4"]


        self._selected_note_id = None
        self._selected_note_id_color = "StepSequencer.NoteEditor.Playing"

        # matrix
        if matrix != None:
            self.set_matrix(matrix)


    def disconnect(self):
        self._matrix = None
        self._velocity_button = None
        self._clip = None

    @property
    def is_multinote(self):
        pass

    def set_multinote(self, is_mutlinote, number_of_lines_per_note):
        pass

    @property
    def quantization(self):
        return self._quantization

    def set_quantization(self, quantization):
        pass

    def set_scale(self, scale):
        pass

    def set_diatonic(self, diatonic):
        pass

    @property
    def key_indexes(self):
        pass

    def set_key_indexes(self, key_indexes):
        pass

    def set_key_index_is_in_scale(self, key_index_is_in_scale):
        pass

    def set_key_index_is_root_note(self, key_index_is_root_note):
        pass

    @property
    def height(self):
        return self._height

    def set_height(self, height):
        self._control_surface.log_message(f"set height to = {height}")
        self._height = height #min(height, 4)

    @property
    def width(self):
        return self._width

    @property
    def number_of_lines_per_note(self):
        return self.height

    def set_page(self, page):
        #CK

        # if self.is_multinote:
        #     self._page = page
        # else:
        #     self._page = int(page / 4)  # 4 lines per note (32 steps seq)
        # self._page = int(page / 4)  # 4 lines per note (32 steps seq)
        self._page = page
        self._control_surface.log_message(f"set_page page = {page} ({self._page})")

    def set_clip(self, clip):
        self._clip = clip

    def set_note_cache(self, note_cache):
        # self._note_cache = note_cache
        pass

    def set_playhead(self, playhead):  # Playing cursor
        self._playhead = playhead
        self._update_matrix()

    # def update_notes(self):  # Deprecated ???
    #     if self._clip is not None:
    #         self._update_matrix()

    def shift_up(self):
        self._shift_down = False
    def shift_down(self):
        self._shift_down = True

    def increment_selected_note_velocity(self):
        if self._selected_note_id is not None:
            notes = self._clip.get_notes_by_id([self._selected_note_id])
            if notes[0].velocity <117:
                notes[0].velocity = notes[0].velocity + 10
            else:
                notes[0].velocity = 127

            self._clip.apply_note_modifications(notes)

    def decrement_selected_note_velocity(self):
        if self._selected_note_id is not None:
            notes = self._clip.get_notes_by_id([self._selected_note_id])
            if notes[0].velocity > 10:
                notes[0].velocity = notes[0].velocity - 10
            else:
                notes[0].velocity = 0

            self._clip.apply_note_modifications(notes)

    def decrement_selected_note(self):
        if self._selected_note_id is not None:
            notes = self._clip.get_notes_by_id([self._selected_note_id])
            notes[0].pitch = notes[0].pitch-1
            self._clip.apply_note_modifications(notes)
        else:
            notes = self._clip.get_all_notes_extended()
            for note in notes:
                note.pitch = note.pitch-1

            self._clip.apply_note_modifications(notes)

        self._update_matrix()

    def increment_selected_note(self):
        if self._selected_note_id is not None:
            notes = self._clip.get_notes_by_id([self._selected_note_id])
            notes[0].pitch = notes[0].pitch+1
            self._clip.apply_note_modifications(notes)
        else:
            notes = self._clip.get_all_notes_extended()
            for note in notes:
                note.pitch = note.pitch+1

            self._clip.apply_note_modifications(notes)

        self._update_matrix()

    def shift_clip_notes_right(self):
        notes = self._clip.get_all_notes_extended()
        for note in notes:
            note.start_time = note.start_time + self._quantization

        self._clip.apply_note_modifications(notes)

    def shift_clip_notes_left(self):
        notes = self._clip.get_all_notes_extended()
        for note in notes:
            note.start_time = note.start_time - self._quantization

        self._clip.apply_note_modifications(notes)

    def randomise_notes(self):
        notes = self._clip.get_all_notes_extended()
        for note in notes:
            note.pitch = randrange(60-12, 60+12)

        self._clip.apply_note_modifications(notes)

    def randomise_velocities(self):
        notes = self._clip.get_all_notes_extended()
        for note in notes:
            note.velocity = randrange(20, 127)

        self._clip.apply_note_modifications(notes)

    def half_clip_size(self):
        self._clip.end_marker = self._clip.end_marker / 2
        self._clip.loop_end = self._clip.loop_end / 2

    def double_or_duplicate_clip(self):
        notes = self._clip.get_all_notes_extended()
        furthest_end_time = 0
        for note in notes:
            if furthest_end_time < note.start_time + note.duration:
                furthest_end_time = note.start_time + note.duration

        if furthest_end_time <= self._clip.end_marker:
            self._clip.duplicate_loop()
        else:
            self._clip.end_marker = self._clip.end_marker * 2
            self._clip.loop_end = self._clip.loop_end * 2

    def update(self, force=False):
        self._control_surface.log_message(f"NE update. {self.is_enabled()}")
        if self.is_enabled():
            # if force:
            #     self._force_update = True
            # self._update_velocity_button()
            self._update_matrix()

    def set_matrix(self, matrix):
        if (matrix != self._matrix):
            if (self._matrix != None):
                self._matrix.remove_value_listener(self._matrix_value)
            self._matrix = matrix
            if (self._matrix != None):
                self._matrix.add_value_listener(self._matrix_value)
                self._width = self._matrix.width()
                # self._height = self._matrix.height()
                self._grid_buffer = [[0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0],
                                     [0, 0, 0, 0, 0, 0, 0, 0]
                                     ]

                self._grid_back_buffer = [[0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0]
                                          ]

    def _matrix_value(self, value, x, y, is_momentary):
        if self.is_enabled() and y < self.height:  # Height value can be 8 (MULTINOTE/SCALE_EDIT) or 4 (STEPSEQ_MODE_NORMAL)
            if ((value != 0) or (not is_momentary)):  # if NOTE_ON or button is toggle
                self._stepsequencer._was_velocity_shifted = False  # Some previous state logic INVESTIGATE
                self._matrix_value_message([value, x, y, is_momentary])

    # Add/Delete/Mute notes in the cache for PL light management and in the Live's Clip OK
    def _matrix_value_message(self, values):  # (value=127/0, x=idx, y=idx, is_momentary=True)
        self._control_surface.log_message(f"_matrix_value_message. clip: {self._clip}")
        value = values[0]
        x = values[1]
        y = values[2]
        is_momentary = values[3]
        """(pitch, time, note_duration, velocity, mute state)"""
        assert (self._matrix != None)
        assert (value in range(128))
        assert (x in range(self._matrix.width()))
        assert (y in range(self._matrix.height()))
        assert isinstance(is_momentary, type(False))

        pitch = 60
        velocity = 120
        note_duration = 0.25
        start_time = 0

        if self.is_enabled() and self._clip == None:
            self._stepsequencer.create_clip()
        elif self.is_enabled() and self._clip != None:
            if value != 0 or not is_momentary:  # if NOTE_ON or button is toggle
                # note data
                # self._control_surface.log_message(
                #     f"q * (p * w * nlp + y * w + x) = {self.quantization} * ({self._page} * {self.width} * {self.number_of_lines_per_note} + {y} * {self.width} + {x})")
                # self._control_surface.log_message(
                #     f"q * (p * w * nlp + y * w + x) = {self.quantization} * ({self._page * self.width * self.number_of_lines_per_note} + {y * self.width} + {x})")
                # self._control_surface.log_message(
                #     f"q * (p * w * nlp + y * w + x) = {self.quantization} * ({self._page * self.width * self.number_of_lines_per_note + y * self.width + x})")

                start_time = self.quantization * (
                        self._page * self.width * self.number_of_lines_per_note + y * self.width + x)
                self._control_surface.log_message(f"start_time: {start_time}")
                pitch = 60
                velocity = 127
                note_duration = 0.25  # setted by quantization button in StepSequencerComponent

                # TODO: use new better way for editing clip

        all_notes = self._clip.get_all_notes_extended()


        for note in all_notes:
            if start_time == note.start_time: # Exists
                if self._shift_down:
                    if note.note_id == self._selected_note_id:
                        self._selected_note_id = None

                    self._clip.remove_notes_extended(0, 127, start_time, note.duration)
                elif note.note_id == self._selected_note_id:
                    self._selected_note_id = None
                elif note.note_id != self._selected_note_id:
                    self._selected_note_id = note.note_id
                elif self._selected_note_id is None:
                    self._selected_note_id = note.note_id
                break
        else:
            new_note = Live.Clip.MidiNoteSpecification(pitch=pitch,
                                                   start_time=start_time,
                                                   duration=note_duration,
                                                   velocity=velocity)

            self.new_note_id = self._clip.add_new_notes([new_note])[0]
            # self._selected_note_id = SelectedNote((x, y), new_note_id)

        # self._control_surface.log_message(f"self._selected_note_id at end       = {self._selected_note_id}")
        self._update_matrix()



    def _update_matrix(self):
        # self._control_surface.log_message(f"CK NE update_matrix. {self.is_enabled()}, {self._matrix}, clip:{self._clip}, _note_cache: {self._note_cache}")
        if self.is_enabled() and self._matrix != None:
            # self._control_surface.log_message(f"update matrix self.height = {self.height}")
            # clear back buffer
            for x in range(self.width):
                for y in range(self.height):
                    self._grid_back_buffer[x][y] = "DefaultButton.Disabled"

            # update back buffer
            if self._clip != None:# and self._note_cache != None:

                # play back position
                if self._playhead != None:
                    play_position = self._playhead  # position in beats (integer = number of beats, decimal subdivisions)
                    play_page = int(play_position / self.quantization / self.width / self.number_of_lines_per_note)
                    play_row = int(play_position / self.quantization / self.width) % self.number_of_lines_per_note
                    play_x_position = int(play_position / self.quantization) % self.width
                    play_y_position = int(play_position / self.quantization / self.width) % self.height
                else:
                    play_position = -1
                    play_page = -1
                    play_row = -1
                    play_x_position = -1
                    play_y_position = -1
                # add play positition in amber
                if (self.display_metronome):
                    if self._clip.is_playing and self.song().is_playing:
                        self._grid_back_buffer[play_x_position][play_y_position] = "StepSequencer.NoteEditor.Metronome"

                # Display the selected page # CK _display_selected_page is only for multinote
                # if (self._display_page):
                #     self._display_selected_page()
                #     if self._display_page_time + 0.25 < time.time():
                #         self._display_page = False

                # Display the notes in the 1st left column
                # if self.is_multinote:
                #     self._display_note_markers()
                #     # Display the current played page
                #     if (self._current_page != play_page):
                #         self._current_page = play_page
                #         self._display_current_page()

                # display clip notes
                for note in self._clip.get_all_notes_extended(): #self._note_cache:
                    note_position = note.start_time # note[1]  # decimal value of a beat (1=beat, same as playhead)
                    note_key = note.pitch  #note[0]  # key: 0-127 MIDI note #
                    note_velocity =  note.velocity #note[3]  # velocity: 0-127 value #

                    # self._control_surface.log_message(f"note pos = {note_position}")
                    # self._control_surface.log_message(f"self.width/height = {self.width}/{self.height}")
                    # self._control_surface.log_message(f"self.number_of_lines_per_note = {self.number_of_lines_per_note}")
                    # self._control_surface.log_message(f"self.quantization = {self.quantization}")

                    note_page = int(note_position / self.quantization / self.width / self.number_of_lines_per_note)
                    note_grid_x_position = int(note_position / self.quantization) % self.width
                    note_grid_y_position = int(note_position / self.quantization / self.width) % self.height

                    #0.25 = 1
                    #0.5 = 2
                    #0.75 = 3
                    #1.0 = 4
                    #1.25 = 5
                    #1.5 = 6
                    #1.75 = 7

                    # self._control_surface.log_message(f"note_page = {note_page}")
                    # self._control_surface.log_message(f"play_page = {play_page}")
                    # self._control_surface.log_message(f"play_row = {play_row}")
                    # self._control_surface.log_message(f"self page = {self._page}")
                    #
                    # self._control_surface.log_message(f"note_grid_x_position = {note_grid_x_position}")
                    # self._control_surface.log_message(f"note_grid_y_position = {note_grid_y_position}")

                    velocity_color = self.velocity_color_map[0]
                    for index in range(len(self.velocity_map)):
                        if note_velocity >= self.velocity_map[index]:
                            velocity_color = self.velocity_color_map[index]


                    self._grid_back_buffer[note_grid_x_position][note_grid_y_position] = velocity_color

                    # if self._selected_note_id_id is not None:
                    # self._control_surface.log_message(f"_update self._selected_note_id = {self._selected_note_id} == {note.note_id}")

                    if note.note_id == self._selected_note_id:
                        self._grid_back_buffer[note_grid_x_position][note_grid_y_position] = self._selected_note_id_color

                    # Calculate note position in the grid (note position to matrix button logic)
                    # if self.is_multinote:
                    #     # compute base note, taking into account number_of_lines_per_note
                    #     try:
                    #         note_idx = self.key_indexes.index(note_key)
                    #     except ValueError:
                    #         note_idx = -1
                    #     note_grid_y_base = note_idx * self.number_of_lines_per_note
                    #     if (note_grid_y_base >= 0):
                    #         note_grid_y_base = (7 - note_grid_y_base) - (self.number_of_lines_per_note - 1)
                    #     if (note_grid_y_base < 0):
                    #         note_grid_y_base = -1
                    #
                    #     note_grid_y_offset = int(
                    #         note_position / self.quantization / self.width) % self.number_of_lines_per_note
                    # else:
                    idx = 1
            #         try:
            #             idx = self.key_indexes.index(note_key)
            #         except ValueError:
            #             idx = -1
            #
            #         if idx == 0:
            #             note_grid_y_base = 0
            #         else:
            #             note_grid_y_base = -1
            #         note_grid_y_offset = int(
            #             note_position / self.quantization / self.width) % self.number_of_lines_per_note
            #
            #         if note_grid_y_base != -1 and note_grid_y_base < self.height:
            #             note_grid_y_position = note_grid_y_base + note_grid_y_offset
            #         else:
            #             note_grid_x_position = -1
            #             note_grid_y_position = -1
            #
            #         # Set note color
            #         if (note_grid_x_position >= 0):
            #             # compute colors
            #             velocity_color = self.velocity_color_map[0]
            #             for index in range(len(self.velocity_map)):
            #                 if note_velocity >= self.velocity_map[index]:
            #                     velocity_color = self.velocity_color_map[index]
            #             # highligh playing notes in red. even if they are from other pages.
            #             if not note_muted \
            #                     and note_page == play_page \
            #                     and play_x_position == note_grid_x_position \
            #                     and ( play_y_position == note_grid_y_position
            #                           and not self.is_multinote
            #                           or self.is_multinote
            #                           and note_grid_y_offset == play_row)\
            #                     and self.song().is_playing and self._clip.is_playing:
            #                 self._grid_back_buffer[note_grid_x_position][
            #                     note_grid_y_position] = self.playing_note_color
            #             elif note_page == self._page:  # if note is in current page, then update grid
            #                 # do not erase current note highlight
            #                 if self._grid_back_buffer[note_grid_x_position][
            #                     note_grid_y_position] != self.playing_note_color:
            #                     if note_muted:
            #                         self._grid_back_buffer[note_grid_x_position][
            #                             note_grid_y_position] = self.muted_note_color
            #                     else:
            #                         self._grid_back_buffer[note_grid_x_position][
            #                             note_grid_y_position] = velocity_color
            #
            #     # Display the column to show the page for half a second
            #     if self._display_page:
            #         if time.time() - self._display_page_time > 0.5:
            #             self._display_page = False
            #         self._display_selected_page()
            #
            # caching : compare back buffer to buffer and update grid. this should minimize midi traffic quite a bit.
            for x in range(self.width):
                for y in range(self.height):
                    if self._grid_back_buffer[x][y] != self._grid_buffer[x][y] or self._force_update:
                        self._grid_buffer[x][y] = self._grid_back_buffer[x][y]
                        self._matrix.get_button(x, y).set_light(self._grid_buffer[x][y])
            self._force_update = False
