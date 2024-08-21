from raya.enumerations import UI_ANIMATION_TYPE, UI_THEME_TYPE, UI_TITLE_SIZE
import time

background_logo = 'url(/assets/background.png)'

THEME = UI_THEME_TYPE.WHITE

USER_CHOICES_TO_VOICE = {1 : 'VOICE_MEMORY_GAME',
                         2 : 'VOICE_SIMON_GAME',
                         3 : 'TBD',
                         4 : 'VOICE_DIFFICULTY_EASY',
                         5 : 'VOICE_DIFFICULTY_MEDIUM',
                         6 : 'VOICE_DIFFICULTY_HARD'
                        }

USER_CHOICES_TO_NAME = {1 : 'Memory Game',
                        2 : 'Simon Game',
                        3 : 'Finish',
                        4 : 'Easy',
                        5 : 'Medium',
                        6 : 'Hard'
                    }

CUSTOM_STYLE = {'title' : {'font-size' : '150px'},
                        'subtitle' : {'font-size' : '70px'},
                        'background' : {'background' : background_logo,
                                        'backgroundRepeat' : 'no-repeat',
                                        'backgroundSize' : 'cover'}
                }

CUSTOM_STYLE_GAMES = {'title' : {'font-size' : '75px'},
                        'subtitle' : {'font-size' : '70px'},
                        'background' : {'background' : background_logo,
                                        'backgroundRepeat' : 'no-repeat',
                                        'backgroundSize' : 'cover'}
                }

UI_GAME_CHOICE_SELECTOR = {
    'title' : 'What would you like to play today?',
    'show_back_button' : False,
    'data' : [{
        'id' : 1,
        'name' : 'Memory Game',
        'imgSrc' : '/assets/memory_game.png'
    }, {
        'id' : 2,
        'name' : 'Simon Game',
        'imgSrc' : '/assets/simon_game.png'
    }, {
        'id' : 3,
        'name' : 'Finish App',
        'imgSrc' : '/assets/TBD.png'
    }],
    'theme' : THEME,
    'title_size' : UI_TITLE_SIZE.LARGE,
    'custom_style' : {'title' : {'font-size' : '80px'},
                        'subtitle' : {'font-size' : '50px'},
                        "selector": {"background-color": "white",
                                    "border-width": "4px",
                                    "border-color": "#0686D8"
                                },
                        'background' : {'background' : background_logo,
                                        'backgroundRepeat' : 'no-repeat',
                                        'backgroundSize' : 'cover'}}
    }

UI_DIFFICULTY_CHOICE_SELECTOR = {
    'title' : 'Select your difficulty level',
    'show_back_button' : True,
    'data' : [{
        'id' : 4,
        'name' : 'Easy',
        'imgSrc' : '/assets/easy_level.png'
    }, {
        'id' : 5,
        'name' : 'Intermediate',
        'imgSrc' : '/assets/medium_level.png'
    }, {
        'id' : 6,
        'name' : 'Advanced',
        'imgSrc' : '/assets/hard_level.png'
    }],
    'theme' : THEME,
    'title_size' : UI_TITLE_SIZE.LARGE,
    'custom_style' : {'title' : {'font-size' : '80px'},
                        'subtitle' : {'font-size' : '50px'},
                        "selector": {"background-color": "white",
                                    "border-width": "4px",
                                    "border-color": "#0686D8"
                                },
                        'background' : {'background' : background_logo,
                                        'backgroundRepeat' : 'no-repeat',
                                        'backgroundSize' : 'cover'}}
    }

UI_WELL_DONE = {
    'title' : '',
    'show_back_button' : False,
    'content' : '/assets/well_done.png',
    'format' : UI_ANIMATION_TYPE.URL,
    'custom_style' : {'title' : {'font-size' : '80px'},
                        'subtitle' : {'font-size' : '50px'},
                        "selector": {"background-color": "white",
                                    "border-width": "4px",
                                    "border-color": "#0686D8"
                                },
                        'background' : {'background' : background_logo,
                                        'backgroundRepeat' : 'no-repeat',
                                        'backgroundSize' : 'cover'},
                         'image' : {'width' : '700px',
                                    'height' : '700px'}
                                        }
}

SCREENS_ENGLISH = {'UI_GAME_CHOICE_SELECTOR' : UI_GAME_CHOICE_SELECTOR,
                   'UI_DIFFICULTY_CHOICE_SELECTOR' : UI_DIFFICULTY_CHOICE_SELECTOR,
                   'UI_WELL_DONE' : UI_WELL_DONE
                }