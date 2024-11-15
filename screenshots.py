import subprocess
import time
from datetime import datetime
import mss
from PIL import Image, ImageDraw, ImageFont
import os

# THE FOLLOWING CODE ONLY RUN ON A XORG DESKTOP ENVIRONMENT!!!!
# THERE IS CURRENTLY NO WAY TO RUN THIS OR SOMETHING SIMILAR ON WAYLAND AND A DIFFFERENT (AND MORE COMPLEX) APPROACH IS REQUIRED

def get_window_geometry(window_name):
    # Get info about the window from xwininfo as a subprocess
    try:
        output = subprocess.check_output(["xwininfo", "-name", window_name]).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"Unable to find window with name: '{window_name}'")
        exit(1)
    
    # Parse command output and extract window geometry
    geometry = {}
    for line in output.split("\n"):
        if "Absolute upper-left X:" in line:
            geometry['left'] = int(line.split(":")[1].strip())
        elif "Absolute upper-left Y:" in line:
            geometry['top'] = int(line.split(":")[1].strip())
        elif "Width:" in line:
            geometry['width'] = int(line.split(":")[1].strip())
        elif "Height:" in line:
            geometry['height'] = int(line.split(":")[1].strip())
    
    return geometry

# Format geometry data in a way mss can understand
def get_monitor_obj(geometry):
    left = geometry['left']
    top = geometry['top']
    width = geometry['width']
    height = geometry['height']
    
    monitor = {"top": top, "left": left, "width": width, "height": height}
    return monitor

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]

window_title = "Hearthstone"

out_folder = f"test-data/screenshots/{get_timestamp()}"
os.makedirs(out_folder, exist_ok=True)

# Get window geometry and format it
geometry = get_window_geometry(window_title)
monitor = get_monitor_obj(geometry)

# Configure a font to write timestamps
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(font_path):
    # Try and alternative
    font_path = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

font = ImageFont.truetype(font_path, 20)

# Mainloop to capture screenshots
with mss.mss() as sct:
    while True:
        start_time = time.time()

        # the try except block is needed to handle some errors that might be thrown when the window is being moved/manipulated while taking a screenshot
        # excecution should be able to continue from the next cycle, at worse skipping a few
        try:
            # Update area to capture
            monitor = get_monitor_obj(get_window_geometry(window_title))
            
            # Capture the screenshot with the info given
            img = sct.grab(monitor)

        except mss.exception.ScreenShotError:
            print(f"Encountered an error while taking a screenshot at {get_timestamp()}\nContinuing normally from the next cycle\n")
            continue

        # Add the timestamp to te image
        img_pil = Image.frombytes('RGB', img.size, img.rgb)
        draw = ImageDraw.Draw(img_pil)
        draw.text((10, 10), get_timestamp(), font=font, fill="white")
        
        # Save the image
        filename = f"{out_folder}/screenshot_{get_timestamp()}.png"
        img_pil.save(filename)
        
        # Compute time taken to take a screenshot --- optional
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 0.5 - elapsed_time)  # This sets the frequency, taking into consideration what we want and what the computer can currently do
        time.sleep(sleep_time)
