import time
import pyautogui

# Wait 3 seconds before starting
time.sleep(3)

# Define range (N to M)
N = 1
M = 10  # Adjust M to your desired end value

for i in range(N, M + 1):
    # Type the number
    pyautogui.typewrite(str(i))
    time.sleep(0.2)
    
    # Press Tab
    pyautogui.press('tab')
    time.sleep(0.2)
    
    # Type "Team" + number
    pyautogui.typewrite('Team ' + str(i))
    time.sleep(0.2)
    
    # Press Tab
    pyautogui.press('tab')
    time.sleep(0.2)
    
    # Press Enter
    pyautogui.press('enter')
    time.sleep(0.2)
    
    # Press Shift+Tab
    pyautogui.hotkey('shift', 'tab')
    time.sleep(0.2)

    # Press Shift+Tab
    pyautogui.hotkey('shift', 'tab')
    time.sleep(0.2)
