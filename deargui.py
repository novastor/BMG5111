#https://github.com/hoffstadt/DearPyGui/discussions/1596

from reactpy import component, html, run
from utils.stateful_scheduling import search_with_rag as rag
from utils import realtime_whisper as am
from dotenv import load_dotenv
import string
import sys
import dearpygui.dearpygui as dpg
audio_filename = "scheduling.m4a"
index_name = "scheduler-vectorised"



dpg.create_context()
# dpg is imported somewhere earlier in the file as follows:
# import dearpygui.dearpygui as dpg

def record(sender, app_data, user_data):
  dpg.add_text("loading",parent="inputs")  
  #load_dotenv()
  # Unpack the user_data that is currently associated with the button
  state, enabled_theme, disabled_theme = user_data
  # Flip the state
  state = not state
  # Apply the appropriate theme
  dpg.bind_item_theme(sender, enabled_theme if state is True else disabled_theme)
  # Update the user_data associated with the button
  dpg.set_item_user_data(sender, (state, enabled_theme, disabled_theme,))
  text =  am.audio_processing()
  print(text)
  f = open("utils/target.txt", "w")
  f.write(str(text))
  f.close()
  dpg.set_value("l1","loading complete")

# Define your themes and button somewhere in your code
# - This theme should make the label text on the button white
def generate(sender, app_data, user_data):
  # Unpack the user_data that is currently associated with the button
  state, enabled_theme, disabled_theme = user_data
  # Flip the state
  state = not state
  # Apply the appropriate theme
  dpg.bind_item_theme(sender, enabled_theme if state is True else disabled_theme)
  # Update the user_data associated with the button
  dpg.set_item_user_data(sender, (state, enabled_theme, disabled_theme,))
  f = open('utils/mockup.txt', 'r')
  content = f.read()
  f.close()
  result = rag(index_name,content)
  print(result)
  sub = ","
  location = result.split(sub)[0]
  desc = result.split(sub)[1]
  idx = result.split(sub)[2]
  time = result.split(sub)[3]
  mach = result.split(sub)[4]
  print("\033[H\033[J", end="")
  print("location on patient : " +location)
  print("identified condition : " +desc)
  print("severity : " +idx)
  print("time remaining : " +time)
  print("unit required: " +mach)

with dpg.window(label="Schedule preview", modal=True, show=False, tag="modal_id", no_title_bar=False):
    f = open('utils/target.txt', 'r')
    content = f.read()
    f.close()
    result = rag(index_name,content)
    print("result")
    print(result)
    result = result["answer"]
    sub = ","
    alist  = []
    location = result.split(sub)[0]
    alist.append(location)
    desc = result.split(sub)[1]
    alist.append(desc)
    idx = result.split(sub)[2]
    alist.append(idx)
    time = result.split(sub)[3]
    alist.append(time)
    mach = result.split(sub)[4]
    alist.append(mach)
  #print("\033[H\033[J", end="")
  #print("location on patient : " +location)
  #print("identified condition : " +desc)
  #print("severity : " +idx)
  #print("time remaining : " +time)
  #print("unit required: " +mach)
    dpg.add_text("Displaying request information.\n Please verify all data is correct")
    dpg.add_separator()
    with dpg.table(header_row=True, row_background=True,
                   borders_innerH=True, borders_outerH=True, borders_innerV=True,
                   borders_outerV=True):
        
        # use add_table_column to add columns to the table,
        # table columns use child slot 0
        dpg.add_table_column(label="scan location")
        dpg.add_table_column(label="condition")
        dpg.add_table_column(label="severity index")
        dpg.add_table_column(label="max time")
        dpg.add_table_column(label="unit required")
        # add_table_next_column will jump to the next row
        # once it reaches the end of the columns
        # table next column use slot 1
        for i in range(0,1):
            with dpg.table_row():
                for j in range(0, 5):
                    dpg.add_text(alist[j])
                    print(alist[j])
    dpg.add_checkbox(label="confirm schedule")

# Define your themes and button somewhere in your code
# - This theme should make the label text on the button white
with dpg.theme() as enabled_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Button, (192, 192, 192), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (65, 65, 65), category=dpg.mvThemeCat_Core)
# - This theme should make the label text on the button red
with dpg.theme() as disabled_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Button, (192, 192, 192), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core)
with dpg.theme() as global_theme:

    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 140, 23), category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
        
    with dpg.theme_component(dpg.mvInputInt):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 23), category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10, category=dpg.mvThemeCat_Core)


# - Create the button, assign the callback function, and assign the initial state (e.g. True) and the themes as user_data
with dpg.window(tag="primary window"):
        dpg.add_text("Medical triage scheduler")
        with dpg.group(horizontal=True,tag="inputs"):
          dpg.add_button(label="listen and record", callback=record, user_data=(True, enabled_theme, disabled_theme,),tag="R_B")
          dpg.add_button(label="update procedure schedule", callback=lambda: dpg.configure_item("modal_id", show=True))
       
dpg.bind_theme(global_theme)
dpg.create_viewport(title='Inventory scheduler', width=500, height=150)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("primary window", True)
dpg.start_dearpygui()
dpg.destroy_context()