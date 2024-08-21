# Raya Imports
from raya.application_base import RayaApplicationBase
from raya.controllers import *
from raya.enumerations import *
from res.constants import *
from res.audio_english import AUDIO_ENGLISH
from res.ui_english import SCREENS_ENGLISH, CUSTOM_STYLE_GAMES, USER_CHOICES_TO_NAME, USER_CHOICES_TO_VOICE
from raya.tools.filesystem import *
from google.cloud import texttospeech

# Other Imports
import os
import time
import numpy as np
import argparse

# Others
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'client_service_key_2.json'
AUDIO_language_dict = {'ENGLISH' : AUDIO_ENGLISH}
UI_language_dict = {'ENGLISH' : SCREENS_ENGLISH}


class RayaApplication(RayaApplicationBase):

    async def setup(self):
        # Get app args
        self.get_args()

        # Setup variables   
        self.setup_variables()

        # Reset user feedbacks
        self.reset_user_feedbacks()
    
        # Enable controllers
        await self.enable_controllers()

        # Create listeners
        await self.create_listeners()     

        # Redownload voices, currently operating with debug flag
        if self.debug:
            await self.debug_sequence()
            self.finish_app()

        # Get the audio (sound controller patch)
        await self.get_buffers_dict(dynamic = True)
        self.temp_get_audio()


    async def loop(self):
        # Choose the game
        game_choice_name = await self.base_choice_selector(
                                screen = UI_GAME_CHOICE_SELECTOR,
                                voice = f'VOICE_PLAY_WITH_ME_{self.language}',
                                voice_override = self.voice_override
                            )
        self.voice_override = True
        if game_choice_name == 'Finish':
            self.finish_app()

        # Choose the difficulty
        difficulty_choice_name = await self.base_choice_selector(
                            screen = UI_DIFFICULTY_CHOICE_SELECTOR,
                            voice = f'VOICE_CHOOSE_DIFFICULTY_{self.language}'
                        )
        
        # Restart the loop if the user pressed the back button in difficulty
        # choice selector
        if difficulty_choice_name is None:
            return
        
        await self.play_predefined_sound_v2(
            self.combined_dict[
                f'VOICE_DIFFICULTY_{difficulty_choice_name.upper()}_{self.language}'])

        # Play the game
        if game_choice_name == 'Memory Game':
            self.memory_game_difficulty = difficulty_choice_name
            await self.memory_game()
        elif game_choice_name == 'Simon Game':
            self.simon_game_difficulty = difficulty_choice_name
            await self.simon_game()


    async def finish(self):
        # Finishing instructions
        self.log.warn(f'Hello from finish()')
        await self.fleet.finish_task(task_id=self.task_id,
                                           result=FLEET_FINISH_STATUS.SUCCESS,
                                           message='Done!')

    

### -------------------------------- Helpers --------------------------------###

    def get_args(self):
        parser = argparse.ArgumentParser()

        # Initial navigation position (X, Y, angle) and name
        parser.add_argument('-x' , '--target_x',
                            type = float, default = 5.0, required = False,
                            help ='X coordinate to initial navigation')
        
        parser.add_argument('-y', '--target_y',
                            type = float, default = 5.0, required = False,
                            help = 'Y coordinate to initial navigation')
        
        parser.add_argument('-a', '--target_angle',
                            type = float, default = 5.0, required = False,
                            help = 'Angle to initial navigation')

        parser.add_argument('-tn', '--target_name',
                            type = str, default = 'test', required = False,
                            help = 'Name of the location')

        # Task ID
        parser.add_argument('-tid', '--task_id',
                            type = str, default = 1,
                            required = False, help = 'Task ID')
        
        # Memory Game Difficulty
        parser.add_argument('-md', '--memory_game_difficulty',
                            type = str, default = 'Easy',
                            required = False, help = 'Memory game level')
        
        # Simon Game Difficulty
        parser.add_argument('-sd', '--simon_game_difficulty',
                            type = str, default = 'Easy',
                            required = False, help = 'Simon game level')

        # Language to speak
        parser.add_argument('-l', '--language',
                            type = str, default = 'english',
                            required = False, help = 'language')
        
        # Debug flag
        parser.add_argument('-db', '--debug_flag',
                            type = bool, default = False,
                            required = False, help = 'debug flag')
        
        
        # Parse the arguments
        args, unknown_args = parser.parse_known_args()
        self.x = args.target_x
        self.y = args.target_y
        self.angle = args.target_angle
        self.target_name = args.target_name
        self.task_id = args.task_id
        self.memory_game_difficulty = args.memory_game_difficulty
        self.simon_game_difficulty = args.simon_game_difficulty
        self.debug = args.debug_flag
        self.language = args.language.upper()

        # Update the audio constants file with the patient name
        self.audio_dict = AUDIO_language_dict[self.language]

        # Take the relevant screens according to the chosen language
        globals().update(UI_language_dict[self.language])


    async def debug_sequence(self):
        self.log.debug('DEBUG MODE - DOWNLOADING AUDIO')
        await self.download_all_voices()
        await self.get_buffers_dict(dynamic = False),
        self.temp_get_audio()


    async def enable_controllers(self):
        self.ui: UIController = await self.enable_controller('ui')
        self.log.info('UI controller - Enabled')
        self.leds: LedsController = await self.enable_controller('leds')
        self.log.info('Leds controller - Enabled') 
        self.sound: SoundController = await self.enable_controller('sound')
        self.log.info('Sound controller - Enabled')
        self.fleet: FleetController = await self.enable_controller('fleet')
        self.log.info('Fleet controller - Enabled')
        

    async def create_listeners(self):
        '''Create fleet and chest button listeners for treatment cancellation'''
        self.fleet.set_msgs_from_fleet_callback(
                                callback = self.cb_fleet_messages,
                                callback_async = self.async_cb_fleet_messages)

    async def simon_game(self):
        '''Open a simon says game session'''

         # Reset feedback
        self.reset_user_feedbacks()        
        await self.ui.open_game(
                        game = 'SimonGame',
                        difficulty = self.simon_game_difficulty,
                        back_button_text = '',
                        button_text = 'Begin',
                        title = 'Simon Says',
                        show_start_modal = True,
                        start_button_timeout = 5.0,
                        theme = UI_THEME_TYPE.WHITE,
                        chosen_language = self.language[:2].lower(),
                        wait = False,
                        end_game_text = 'End Game',
                        feedback_callback_async = self.async_cb_feedback_games,
                        finish_callback_async = self.async_cb_finish_games,
                        custom_style = CUSTOM_STYLE_GAMES
                        )
        
        # Explain the game
        await self.play_predefined_sound_v2(
            self.combined_dict[f'VOICE_SIMON_GAME_{self.language}'])

        # Repeat the instructions every 10 seconds until the game started
        num_instructions_reps = 0
        last_feedback = self.games_feedback
        start_time, current_time = time.time(), time.time()
        while self.games_feedback['action'] == None and  \
                                                    num_instructions_reps < 3:
            await self.sleep(1.0)
            current_time = time.time()
            if abs(current_time - start_time) >= 30:
                num_instructions_reps += 1
                await self.play_predefined_sound_v2(
                    self.combined_dict[f'VOICE_SIMON_GAME_{self.language}'])
                start_time = time.time()
        last_feedback = self.games_feedback

        
        # Give the patient feedback until the game is complete
        last_stage = self.games_feedback['stage']
        last_feedback = self.games_feedback.copy()
        i, j = 0, 2
        while self.games_feedback['action'] != 'game-completed':
            # Stop condition
            if self.stop_condition:
                return
            
            # Incorrect card match feedback
            if not self.games_feedback['last_try_success'] and \
                                    self.games_feedback != last_feedback:
                last_feedback = self.games_feedback.copy()                    
                if i%2 == 0:
                    voice = self.choose_random_fail_voice()
                    await self.play_predefined_sound_v2(
                                                    self.combined_dict[voice])
                i += 1

            # Break if stop condition
            if self.ui_button_feedback == 'button_pressed':
                break

            await self.sleep(1.0)

        # Congratulate the patient upon game completion
        await self.ui.display_animation(**UI_WELL_DONE)
        await self.play_predefined_sound_v2(
            self.combined_dict[f'VOICE_GAME_COMPLETED_{self.language}'])

    async def memory_game(self):
        '''Open a memory game session'''

        # Reset feedback
        self.reset_user_feedbacks()
        await self.ui.open_game(
                        game = 'MemoryGame',
                        difficulty = self.memory_game_difficulty,
                        back_button_text = '',
                        title = 'Memory Game',
                        button_text = 'Begin',
                        loaderText = 'Good luck!',
                        loaderTime = '5',
                        theme = UI_THEME_TYPE.WHITE,
                        show_start_modal = True,
                        start_button_timeout = 5.0,
                        chosen_language = self.language[:2].lower(),
                        wait = False,
                        end_game_text = 'End Game',
                        feedback_callback_async = self.async_cb_feedback_games,
                        finish_callback_async = self.async_cb_finish_games,
                        custom_style = CUSTOM_STYLE_GAMES
                        )
        
        # Explain the game
        await self.play_predefined_sound_v2(
            self.combined_dict[f'VOICE_MEMORY_GAME_{self.language}'])
       
        # Give the patient feedback until the game is complete
        last_feedback = self.games_feedback.copy()
        i = 0
        while self.games_feedback['action'] != 'game-completed':
            # Stop condition
            if self.stop_condition:
                return

            # Correct card match feedback
            if self.games_feedback['last_try_success'] and \
                                     self.games_feedback != last_feedback:
                last_feedback = self.games_feedback.copy()
                if self.games_feedback['completed_cards'] == 2:
                    await self.play_predefined_sound_v2(
                        self.combined_dict[
                            f'VOICE_CARD_MATCH_1_{self.language}'])
                elif self.games_feedback['completed_cards'] == \
                                 self.games_feedback['amount_of_cards']-2:
                    await self.play_predefined_sound_v2(
                        self.combined_dict[
                            f'VOICE_CARD_MATCH_LAST_{self.language}'])
                else:
                    voice = self.choose_random_success_voice()
                    await self.play_predefined_sound_v2(
                                                    self.combined_dict[voice])
        

            # Incorrect card match feedback
            elif not self.games_feedback['last_try_success'] and \
                self.games_feedback['failed_attempts'] != \
                                            last_feedback['failed_attempts']:
                last_feedback = self.games_feedback.copy()        
                if i%2 == 0:
                    voice = self.choose_random_fail_voice()
                    await self.play_predefined_sound_v2(
                                                    self.combined_dict[voice])
                else:
                    await self.play_predefined_sound_v2(
                                    self.combined_dict['wrong_answer_sound'])
                i += 1
        

            # Break if stop condition
            if self.ui_button_feedback == 'button_pressed':
                break

            await self.sleep(1.0)

        # Congratulate the patient upon game completion
        await self.ui.display_animation(**UI_WELL_DONE)
        await self.play_predefined_sound_v2(
            self.combined_dict[f'VOICE_GAME_COMPLETED_{self.language}'])
    

    async def play_predefined_sound_v2(self,
                                       recording_name: str,
                                       leds: bool = True,
                                       wait: bool = True
                                       ):
        """"
        Play predefined sound with the sound controller patch
        INPUTS:
                recording_name - name of the audio file to play
                leds - whether to turn on the leds whilst playing the audio
                wait - whether to wait for the audio to finish or not

        OUTPUTS:
                This function doesn't return any outputs, it plays a recording
        """

        buffer_id = recording_name['buffer_id']
        rec_time = recording_name['timestamp']

        leds_data = {'group' : 'head',
                        'color' : 'blue',
                        'animation' : 'MOTION_4',
                        'speed' : 7,
                        'repetitions' : int(0.3*rec_time)+1,
                        'wait' : False
                        }
        try:
            await self.sound.cancel_all_sounds()
            await self.leds.turn_off_group(group = 'head')
        
        except Exception as e:
            self.log.debug(
                f"Couldn't cancel sounds and leds \
                            in play_predefined_sound_v2, got exception - {e}" )

        try:
            self.sound._playing_buffers_ids.update(BUFFER_IDS)
            await self.sound._play_buffer(
                                buff_id = buffer_id,
                                leds = leds,
                                leds_data = leds_data,
                                wait = wait
                                )

        except Exception as e:
            self.log.debug(f"Couldn't play sound {recording_name} \
                               got exception - {e}")



    async def get_buffers_dict(self,
                                leds: bool = False,
                                wait: bool = True,
                                save: bool = False,
                                buffer_id: str = None,
                                dynamic: bool = True
                                ):
        '''
        Get the dictionary containing the buffer ids with their corresponding
        recording name. The function plays each sound and assigns it to a buffer
        INPUTS:
            leds - whether to play leds (the param is required in the sound
                    controller patch, its auto set to False in this wrapper)
            wait - whether to wait when playing the sound
            save - whether to save the sound
            buffer_id - buffer to assign (the param is required in the sound
                        controller patch, its auto set to None in order to
                        generate a buffer id)
            dynamic - whether to assign a buffer to a recording or not if it
                      already exists

        OUTPUTS:
            This function has no outputs. It sets a buffer dictionary attribute
        '''

        # Get the list of recordings to process, depending on whether all
        # voices should be downloaded, or just dynamic ones
        path = f'{AUDIO_PATH}'
        i = 1
        self.rec_times = {}
        recordings_list = os.listdir(resolve_path(path)) if not dynamic else \
                                            self.dynamic_recordings_list
        
        # Play the recording, assign a buffer ID to it
        for recording in recordings_list:
            print(
                f'playing recording: {recording} | [{i}/{len(recordings_list)}]')
            try:
                if self.sound.is_playing():
                    await self.sound.cancel_all_sounds()

                start_time = time.time()
                await self.sound.play_sound(
                                path=f'{AUDIO_PATH}/{recording}',
                                callback_finish = self.cb_finish_sound,
                                wait = wait,
                                save = save,
                                leds = leds,
                                leds_data = {},
                                volume = 0,
                                buffer_id = buffer_id
                                )
                end_time = time.time()
                self.rec_times[recording] = abs(end_time-start_time)
                print(f'time: {abs(end_time-start_time)}'),
                print('-'*75)

            except Exception as e:
                self.log.debug(f'got exception - {e} in get_buffers_dict')
            i += 1
        
        # Print the results
        self.current_buffer_dict = self.sound._get_audio_dict()
        print('-'*100)
        print('BUFFER DICT:')
        print(self.current_buffer_dict)
        print(f'RECORDING TIMES:')
        print(self.rec_times)


    def combine_dicts(self, dict_ids: dict, dict_timestamps: dict):
        '''
        Combine two dictionaries with the same keys to a new dictionary where
        each value is a dict containing the values of the original dict
        '''
        combined_dict = {}
        for name in dict_ids:
            combined_dict[name] = {
                'buffer_id': dict_ids[name],
                'timestamp': dict_timestamps[name]
            }

        return combined_dict


    def choose_random_success_voice(self):
        '''
        Choose a random voice to play to the patient when they chose a correct
        answer in one of the games
        '''
        rand_num = np.random.uniform()
        if 0 <= rand_num <= 0.33:
            voice = f'VOICE_CARD_MATCH_2_{self.language}'
        elif 0.33 < rand_num <= 0.66:
            voice = f'VOICE_CARD_MATCH_3_{self.language}'
        else:
            voice = f'VOICE_CARD_MATCH_4_{self.language}'

        return voice
    


    def choose_random_fail_voice(self):
        '''
        Choose a random voice to play to the patient when they chose an
        incorrect answer in one of the games
        '''
        rand_num = np.random.uniform()
        if 0 <= rand_num <= 0.5:
            voice = f'VOICE_CARD_MISMATCH_1_{self.language}'
        elif 0.5 < rand_num <= 1.0:
            voice = f'VOICE_CARD_MISMATCH_2_{self.language}'

        return voice
    

    def temp_get_audio(self):
        '''
        Temporary way to get the dictionary with the buffer ID and recording
        time, until we apply the changes to the sound controller that the
        patch currently covers
        '''
        self.static_buffer_dict = self.reverse_dict(BUFFER_IDS)
        self.static_buffer_dict = self.strip_prefix_suffix_from_keys(
                                        orig_dict = self.static_buffer_dict,
                                        prefix = 'dat:tts_audio/'
                                        )
        self.static_buffer_dict = self.strip_prefix_suffix_from_keys(
                                        orig_dict = self.static_buffer_dict,
                                        prefix = '.mp3'
                                        )
        self.rec_times_dict = self.strip_prefix_suffix_from_keys(
                                                        orig_dict = REC_TIMES,
                                                        prefix = '.mp3'
                                                        )


        self.dynamic_buffers_dict = self.reverse_dict(self.current_buffer_dict)
        self.dynamic_buffers_dict = self.strip_prefix_suffix_from_keys(
                                        orig_dict = self.dynamic_buffers_dict,
                                        prefix = 'dat:tts_audio/'
                                        )
        self.dynamic_buffers_dict = self.strip_prefix_suffix_from_keys(
                                        orig_dict = self.dynamic_buffers_dict,
                                        prefix = '.mp3'
                                        )
        

        for item in self.dynamic_recordings_list:
            self.static_buffer_dict[item.strip('.mp3')] = \
                                self.dynamic_buffers_dict[item.strip('.mp3')]
            self.rec_times_dict[item.strip('.mp3')] = self.rec_times[item]

        self.combined_dict = self.combine_dicts(self.static_buffer_dict, self.rec_times_dict)

        print(f'combined dict: {self.combined_dict}')
        print('-'*100)


    async def download_all_voices(self):
        '''Download all of the application voices'''
        create_dat_folder(AUDIO_PATH)
        for voice in self.audio_dict:
            await self.download_voice(**self.audio_dict[voice])


    async def download_voice(self,
                       text: str,
                       file_name: str,
                       language: str = 'en-GB',
                       name: str = 'en-GB-Neural2-B',
                       audio_type: str = 'mp3',
                       dynamic: bool = False
                       ):
        """
        Download a custom voice to the robot
        INPUTS:
                text - A text for the robot to download
                file_name - name to save the audio file
                language - language of the audio
                name - name of the voice from the API's voice list
                audio_type - audio file type (mp3, wav, etc..)
                dynamic - whether to always download the voice, or download it
                          only if it doesn't exist

        OUTPUTS:
                This function doesn't return any outputs, it saves a file
        """

        # Get relevant path
        path = f'{AUDIO_PATH}/{file_name}.{audio_type}'

        # If the voice isn't downloaded already, or dynamic flag is up,
        #  download it
        if not check_file_exists(path) or dynamic is True:
            self.dynamic_recordings_list.append(path.strip(f'/{AUDIO_PATH}'))
            self.log.info(f'Downloading audio: \'{path}\'')
            synthesized_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=name,
                ssml_gender=texttospeech.SsmlVoiceGender.MALE)

            audio_config = texttospeech.AudioConfig(
                                audio_encoding=texttospeech.AudioEncoding.MP3,
                                speaking_rate = 0.9
                                )
            
            response = self.text_to_speech_client.synthesize_speech(
                                                    input=synthesized_input,
                                                    voice=voice,
                                                    audio_config=audio_config
                                                    )
            with open_file(path, 'wb') as gary_response:
                gary_response.write(response.audio_content)


    def reverse_dict(self, original_dict: dict):
        '''Reverse keys and values for dictionary'''
        reversed_dict = {value: key for key, value in original_dict.items()}
        return reversed_dict
    


    def strip_prefix_suffix_from_keys(self, orig_dict: dict, prefix: str):
        '''Strip a chosen prefix from keys of a dictionary'''
        prefix_len = len(prefix)
        new_dict = {}
        for key, value in orig_dict.items():
            if key.startswith(prefix):
                key = key[prefix_len:]
            if key.endswith(prefix):
                key = key[:-prefix_len]
            new_dict[key] = value
        return new_dict


    def setup_variables(self):
        self.simon_game_difficulty = 'Easy'
        self.memory_game_difficulty = 'Easy'
        self.dynamic_recordings_list = []
        self.ui_button_feedback = None
        self.ui_button_feedback_id = None
        self.games_feedback = None
        self.stop_condition = False
        self.voice_override = False
        self.text_to_speech_client = texttospeech.TextToSpeechClient()


    def reset_user_feedbacks(self):
            '''Reset any UI feedback given by the user'''
            self.ui_button_feedback = None
            self.ui_button_feedback_id = None
            self.video_feedback = None
            self.games_feedback = {'action' : None,
                                    'completed_cards' : 0,
                                    'amount_of_cards' : 0,
                                    'failed_attempts' : 0,
                                    'successful_guess' : 0,
                                    'stage' : 1,
                                    'last_try_success' : False
                                    }
            

    async def base_choice_selector(self,
                                 screen: dict,
                                 voice: str,
                                 voice_override = False,
                                 rep_time: int = 30,
                                 ):
        
        # Reset feedbacks
        counter = 0
        self.reset_user_feedbacks()
        await self.ui.display_choice_selector(**screen,
                                              callback = self.cb_ui_feedback,
                                              wait = False
                                              )
        
        while self.ui_button_feedback_id is None:
            if self.stop_condition:
                return
            
            if counter % rep_time == 0 and not voice_override:
                await self.play_predefined_sound_v2(self.combined_dict[voice])

            await self.sleep(1.0)
            counter += 1

         # Activate leds when button is pressed, reset the button feedback
        await self.play_predefined_sound_v2(
            self.combined_dict[f'button_pressed_sound.wav'],
            leds = False,
            wait = False
            )
        await self.turn_on_leds(animation = 'MOTION_10_VER_3',
                            color = 'green',
                            wait = True
                            )  
        
        # Return the user's choice
        if self.ui_button_feedback_id['action'] == 'back_pressed':
            user_choice_name = None
        else:
            user_choice_id = self.ui_button_feedback_id['selected_option']['id']
            user_choice_name = USER_CHOICES_TO_NAME[user_choice_id]

        print(f'user choice name: {user_choice_name}')

        return user_choice_name


    async def wait_for_button(self,
                            screen: dict,
                            rep_time: int = 10,
                            button_type: str = 'start'
                            ):
        '''
        Wait for the user to press a button
        INPUTS:
            screen - the screen to display
            rep_time - the time after which the instructions are repeated if
                        the button is not pressed
            button_type - the type of button, either 'start' to start actions
                        or 'abort' to cancel the treatment

        OUTPUTS:
            The function has no outputs, it simply waits for the user to press
            a button before performing the next action
        '''

        # Reset feedbacks
        self.reset_user_feedbacks()

        # Display start button, start a timer for repeating the instructions
        if button_type == 'start':
            counter = 0
            await self.ui.display_action_screen(**screen,
                                                callback=self.cb_ui_feedback
                                                )
            await self.sleep(1.0)
            counter += 1
        
        # Repeat the instructions every rep_time until button is pressed
        while self.ui_button_feedback != 'button pressed':
            if counter % rep_time == 0:
                if self.stop_condition:
                    return

                if button_type == 'start':
                    await self.play_predefined_sound_v2(
                        self.combined_dict[
                            f'VOICE_PRESS_BUTTON_{self.language}'])

                if button_type == 'abort':
                    await self.play_predefined_sound_v2(
                        self.combined_dict[
                            f'VOICE_ABORT_REASON_{self.language}'])

            await self.sleep(1.0)
            counter += 1

        # Activate leds when button is pressed, reset the button feedback
        await self.play_predefined_sound_v2(
            self.combined_dict[f'button_pressed_sound.wav'],
            leds = False,
            wait = False
            )
        await self.turn_on_leds(animation = 'MOTION_10_VER_3',
                            color = 'green',
                            wait = True
                            )
        
    
    async def turn_on_leds(self,
                           rep_time: int = 3,
                           group: str = 'head',
                           animation: str = 'MOTION_4',
                           color: str = 'BLUE',
                           wait: bool = True
                           ):
        """
        INPUTS:
                rep_time - repetition time in seconds
                group - leds group to turn on (head, skirt, etc..)
                animation - type of animation to play
                color - animation color
                wait - whether to wait for the command to finish or not

        OUTPUTS:
                This function doesn't return any outputs, it turns on the leds
        """
        
        try:
            await self.leds.animation(
                group = group,
                color = color,
                animation = animation,
                speed = 7,
                repetitions = int(0.3 * rep_time) + 1,
                wait = wait)

        except Exception as e:
            self.log.warn(f'Skipped leds, got exception {e}')

### ------------------------------- Callbacks -------------------------------###

    async def async_cb_feedback_games(self, error):
            '''Async callback for games'''
            
            # Pretty display
            if self.games_feedback != error:
                self.log.info(f'Action: {error}')

            # Update feedback
            for key in error:
                self.games_feedback[key] = error[key]
            

    async def async_cb_finish_games(self, error):
        '''Async callback for games finish'''
        for key in error:
            self.games_feedback[key] = error[key]


    def cb_finish_sound(self, status, status_msg):
        pass

    def cb_ui_feedback(self, error, error_msg = 'button pressed'):
        '''Create an async UI callback'''
        try:
            self.create_task(name = 'ui feedback',
                                afunc = self.async_cb_ui_feedback,
                                error = error,
                                error_msg = error_msg
                                )
        except Exception as e:
                pass



    async def async_cb_ui_feedback(self, error, error_msg):
        '''Async UI selectors callback'''
        if self.ui_button_feedback != error_msg:
            self.log.info(f'Action: {error_msg} | ID: {error}')

        if self.sound.is_playing():
            try:
                await self.sound.cancel_all_sounds()
            except Exception as e:
                self.log.warn(f'Got exception {e}, skipping it')

        self.ui_button_feedback = error_msg
        self.ui_button_feedback_id = error

        print(f'ui button feedback: {self.ui_button_feedback}')
        print(f'ui button feedback id: {self.ui_button_feedback_id}')


    def cb_fleet_messages(self, message_dict):
        '''Create an async callback for fleet messages'''
        try:
            self.create_task(name = 'fleet messages',
                             afunc = self.async_cb_fleet_messages,
                             message_dict = message_dict)
        except Exception as e:
            print(f'Error in cb_fleet_messages {e}')


    async def async_cb_fleet_messages(self, message_dict):
        '''Obtain messages sent from the fleet'''
        self.fleet_messages = message_dict.values()

        # Stop the app from the fleet
        if FLEET_STOP_COMMAND in self.fleet_messages:
            self.stop_condition = True
            self.stop_fleet = True