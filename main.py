import time
from os import path
from enum import Enum, auto
import pyautogui
import win32gui
import re
import psutil


class CurrentScreen(Enum):
    NONE = auto()
    PRESS_BUTTON = auto()
    MAIN_SCREEN = auto()
    ONLINE_SCREEN = auto()
    CUSTOM_SCREEN = auto()
    ENTER_KEY = auto()
    CONNECTING = auto()


SCREENSHOTS = {
    'KQB000-push-button-to-start.png': CurrentScreen.PRESS_BUTTON,
    'KQB001a-online-focused.png': CurrentScreen.MAIN_SCREEN,
    'KQB001b-online-not-focused.png': CurrentScreen.MAIN_SCREEN,
    'KQB002a-custom-focused.png': CurrentScreen.ONLINE_SCREEN,
    'KQB002b-custom-not-focused.png': CurrentScreen.ONLINE_SCREEN,
    'KQB003a-spectate-focused.png': CurrentScreen.CUSTOM_SCREEN,
    'KQB003b-spectate-not-focused.png': CurrentScreen.CUSTOM_SCREEN,
    'KQB004-enter-key.png': CurrentScreen.ENTER_KEY,
    'KQB005-connecting-to-custom.png': CurrentScreen.CONNECTING,
}


def get_window_name(handle=None) -> str:
    """
    Returns the window name of the specified handle (from win32gui)
    If no handle is specified then it returns the name of the window that's currently in focus
    :param handle: handle as returned from win32gui methods like GetForegroundWindow, EnumWindows, etc.
    :return: name/title of the window (what's displayed in the top bar)
    """
    if not handle:
        handle = win32gui.GetForegroundWindow()
    return str(win32gui.GetWindowText(handle))


def match_name(input_str: str, match_str: str = 'killer queen black', ignore_case: bool = True) -> re.Match | None:
    """
    Searches a given string for a substring match, more comprehensive than doing a simple 'xyz in random_str'
    It'll return only the part that matches, and you can use regexes, etc.
    :param input_str: the string that you're searching in for matches
    :param match_str: the string that you're looking for. Default: 'killer queen black'
    :param ignore_case: True you want the search to be case-insensitive. Default: True
        if True: 'abc' will match 'abc', 'ABC', 'aBc' etc.
        if False: 'abc' will only match 'abc', not 'ABC', 'aBc' etc.
    :return: re.Match obj for a match, otherwise None. You can use the truthiness to tell if there's a match
    """
    if not match_str:
        match_str = 'killer queen black'
    if ignore_case:
        return re.match(f'.*{match_str}.*', input_str, re.IGNORECASE)
    else:
        return re.match(f'.*{match_str}.*', input_str)


def set_focus(handle, win_search_str: str = 'killer queen black', silent: bool = True):
    """
    Sets the focus to the given window if the window name/title matches the search string
    :param silent:
    :param handle:
    :param win_search_str:
    """
    if not win_search_str:
        win32gui.SetForegroundWindow(handle)
        print(f'Set focus to {get_window_name()}')
        return

    if window_name := get_window_name(handle):
        if match_name(window_name):
            win32gui.SetForegroundWindow(handle)
            print(f'Found match: {win_search_str=} {window_name=} {handle=}')
        else:
            if not silent:
                print(f'No match: {win_search_str=} {window_name=} {handle=}')
    elif not silent:
        print(f'Window has no name {handle=}')


def is_kqb_running():
    for process in psutil.process_iter():
        if match_name(process.name()):
            return True
    return False


def set_kqb_focus(win_search_str: str = 'killer queen black'):
    win32gui.EnumWindows(set_focus, win_search_str)
    return match_name(get_window_name())


def spam_esc(n_times: int = 10, interval: float = 0.05):
    spam_key('esc', n_times, interval)


def spam_key(key_str: str, n_times: int = 10, interval: float = 0.05):
    if key_str not in (keyboard_keys := pyautogui.KEYBOARD_KEYS):
        raise ValueError(f'{key_str} not found in list of keys. Available keys: {keyboard_keys}')
    pyautogui.typewrite([key_str] * n_times, interval=interval)


def spam_left_then_down(n_times: int = 10, interval: float = 0.05):
    spam_key('left', n_times, interval)
    spam_key('down', n_times, interval)


def get_screen(
        confidence: float = 1.0,
        min_confidence: float = 0.7,
        confidence_interval: float = 0.05,
        sleep_interval: float = 0.5,
) -> CurrentScreen:
    """
    iterates through the screenshots trying to determine the correct current screen
    If a match is found, it returns the corresponding CurrentScreen enum
    Otherwise, the confidence is lowered for another pass until a match is found or the confidence drops below the min
    :param confidence: float between 0.5 (low confidence) and 1.0 (exact match) - Default: 1.0
    :param min_confidence: float between 0.5 (low confidence) and 1.0 (exact match) - Default 0.7
        this is the minimum confidence threshold before deciding that the current screen can't be determined
    :param confidence_interval: float between 0.01 and 0.5 - Default: 0.05
        how much to decrement the confidence interval by between runs
    :param sleep_interval: float >= 0.0 - Default: 0.5
        how long (in seconds) to sleep between runs
    :return: CurrentScreen
        if the screen is confidently determined the enum for that screen is returned. Otherwise, CurrentScreen.NONE
    """
    # screenshot is the image, screen is the corresponding CurrentScreen enum
    for screenshot, screen in SCREENSHOTS.items():
        if locate_center(screenshot, confidence):
            return screen
    # if we haven't reached the minimum confidence then sleep for a bit and iterate through once more
    if (confidence := confidence-confidence_interval) > min_confidence:
        time.sleep(sleep_interval)
        return get_screen(confidence, min_confidence, confidence_interval, sleep_interval)
    return CurrentScreen.NONE


def run_kqb(kill_if_running: bool = True, try_n_times: int = 3):
    if kill_if_running and is_kqb_running():
        if set_kqb_focus():
            focus = win32gui.GetForegroundWindow()
            win32gui.CloseWindow(focus)
        else:
            if is_kqb_running():
                raise RuntimeError('KQB is running and can\'t be stopped!')
    elif is_kqb_running():
        return True

    pyautogui.typewrite(['win', ' '], interval=0.5)
    pyautogui.write('killer queen black', interval=0.05)
    pyautogui.press('enter')
    sleep_time = 10.0
    while sleep_time:
        if is_kqb_running():
            return
        sleep_time -= 0.5
        time.sleep(0.5)
    if not is_kqb_running() and try_n_times > 0:
        spam_esc()
        run_kqb(kill_if_running, try_n_times - 1)
    else:
        raise RuntimeError('Cannot start KQB for some reason')


def locate_center(image_filename: str, confidence: float = 0.8, image_dir: str = 'KQB Screenshots'):
    if image_dir:
        image_filename = path.join(image_dir, image_filename)
    try:
        return pyautogui.locateCenterOnScreen(image_filename, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        raise e


def esc_sleep_decrement(sleep_secs: float, sleep_interval: float):
    spam_esc()
    time.sleep(sleep_interval)
    return sleep_secs - sleep_interval


def nav_screens(target_screen: CurrentScreen, sleep_secs: float = 30.0, sleep_interval: float = 0.5):
    if target_screen == CurrentScreen.NONE:
        raise ValueError(f'target_screen cannot be CurrentScreen.NONE')

    if (curr_screen := get_screen()) == target_screen:
        return True
    elif target_screen == CurrentScreen.PRESS_BUTTON:
        raise ValueError(f'Current Screen past {target_screen.name}. '
                         f'Cannot navigate from {curr_screen.name} to {target_screen.name}')

    match curr_screen:
        case CurrentScreen.MAIN_SCREEN:
            spam_left_then_down()
            spam_key('up', 5)
            if locate_center('KQB001a-online-focused.png'):
                pyautogui.press(' ')
            else:
                # tab opens the "friends" menu tab again closes it
                spam_key('tab', 2)
                # spam esc just in case the "friends" menu is still open
                spam_esc()
                sleep_secs = esc_sleep_decrement(sleep_secs, sleep_interval)
        case CurrentScreen.ONLINE_SCREEN:
            if target_screen != CurrentScreen.MAIN_SCREEN:
                spam_left_then_down()
                pyautogui.press('up')
                if locate_center('KQB002a-custom-focused.png'):
                    pyautogui.press(' ')
                else:
                    sleep_secs = esc_sleep_decrement(sleep_secs, sleep_interval)
            else:
                sleep_secs = esc_sleep_decrement(sleep_secs, sleep_interval)
        case CurrentScreen.CUSTOM_SCREEN:
            if target_screen not in (CurrentScreen.MAIN_SCREEN, CurrentScreen.ONLINE_SCREEN):
                spam_left_then_down()
                pyautogui.press('up')
                if locate_center('KQB003a-spectate-focused.png'):
                    pyautogui.press(' ')
                else:
                    sleep_secs = esc_sleep_decrement(sleep_secs, sleep_interval)
            else:
                sleep_secs = esc_sleep_decrement(sleep_secs, sleep_interval)

    if sleep_secs > 0:
        return nav_screens(target_screen, sleep_secs, sleep_interval)
    return False


def spectate_match(spectate_code: str, sleep_secs: int = 30, sleep_interval: float = 0.5):
    if not re.match('^[a-z0-9]{6}$', spectate_code.strip(), re.IGNORECASE):
        raise ValueError(f'Spectate code invalid, should be alphanumeric and 6 chars long {spectate_code=}')
    if is_kqb_running():
        set_kqb_focus()
    else:
        run_kqb()
        set_kqb_focus()

    while (curr_screen := get_screen()) is CurrentScreen.NONE and sleep_secs > 0:
        time.sleep(sleep_interval)
        sleep_secs -= sleep_interval
        print(f'{sleep_secs=}  {curr_screen=}')
    print(f'{curr_screen=}')

    if nav_screens(CurrentScreen.ENTER_KEY):
        spam_key('right')
        spam_key('backspace')
        pyautogui.write(spectate_code, interval=0.05)


if __name__ == '__main__':
    pyautogui.PAUSE = 0.1
    spectate_match('xxxxxx')
    # print(type(win32gui.GetForegroundWindow()))
    # running = pyautogui.locateCenterOnScreen('KQB Screenshots/WIN001a_kqb-running-focused.png')
    # print(running)
    # if not running:
    #     running = pyautogui.locateCenterOnScreen('KQB Screenshots/WIN001b_kqb-running-not-focused.png', confidence=0.8)
    # print(running)
    # if running:
    #     window_focus = None
    #     while not window_focus:
    #         print(window_focus)
    #         window_focus = pyautogui.locateCenterOnScreen('KQB Screenshots/WIN002_kqb-top-bar.png')
    #         if not window_focus:
    #             pyautogui.click(x=running[0], y=running[1])
    #     print(window_focus)
    #     pyautogui.click(x=window_focus[0], y=window_focus[1])
    #     window_focus = pyautogui.locateOnScreen('KQB Screenshots/WIN002_kqb-top-bar.png', confidence=0.8)
    #     print(window_focus)
    #     move_x = window_focus[0] + 100
    #     move_y = pyautogui.size()[1] - window_focus[1] - 500
    #     pyautogui.moveTo(x=move_x, y=move_y, duration=1)
    #     pyautogui.typewrite(['esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc', 'esc'])
