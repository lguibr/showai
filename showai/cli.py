import os
import sys
import time
import argparse
import importlib.util
import threading
import math
import contextlib
import io
import traceback
from rich.live import Live
from rich.align import Align
from rich.text import Text

ASCII_LOGO = r"""
  +===+=               ####*================      
  +=====-..            ########=============      
  =====+-:....         #########+===========      
  +=====--......       ##########===      ==      
   ======+-........    ##########*=====   ==      
    +======*-......... ######### *========**      
     =======+*+:.......=#######  *===========     
        +=====+**+.......:*###### === =========   
          +=====+#*.........   ## ==      ======= 
         =======+*:.......-######*  ============  
      +=======+:.......-#########*  ===========   
    =======+:......... #########*+=========       
   =====+=..........   #########+========         
  +===+:.........      ######**=======            
  ++:.........         ####*=======               
  :........            **+======                  
  .......              =======                    
"""

def generate_rainbow_ascii(frame_num, flash=False):
    lines = ASCII_LOGO.strip("\n").split("\n")
    text = Text()
    
    center_x = max((len(l) for l in lines), default=1) / 2
    center_y = len(lines) / 2
    
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char.isspace():
                text.append(char)
                continue
                
            if flash and frame_num % 10 < 2:
                color = "white"
            else:
                dx = x - center_x
                dy = y - center_y
                angle = math.atan2(dy, dx)
                
                hue = (angle + frame_num * 0.1) % (2 * math.pi)
                r = int((math.sin(hue) + 1) * 127)
                g = int((math.sin(hue + 2 * math.pi / 3) + 1) * 127)
                b = int((math.sin(hue + 4 * math.pi / 3) + 1) * 127)
                
                color = f"rgb({r},{g},{b})"
                
            text.append(char, style=color)
        if y < len(lines) - 1:
            text.append("\n")
            
    return Align.center(text, vertical="middle")

def run_script_internal(script_path, result_container):
    try:
        spec = importlib.util.spec_from_file_location("__main__", script_path)
        if spec is None or spec.loader is None:
            result_container["error"] = f"Failed to load '{script_path}'."
            return
            
        user_module = importlib.util.module_from_spec(spec)
        sys.modules["__main__"] = user_module
        
        # Actually execute the script content
        spec.loader.exec_module(user_module)
        result_container["success"] = True
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
             result_container["error"] = f"Script exited with code {e.code}"
        else:
             result_container["success"] = True
    except Exception as e:
        result_container["error"] = f"Execution Failed: {e}\n{traceback.format_exc()}"

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

def _animation_loop(stop_event):
    from showai.progress import broker
    console = Console(file=sys.__stdout__)
    
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
        expand=True
    )
    
    task_overall = progress.add_task("ShowAI Engine Status", total=100)
    task_audio = progress.add_task("[dim]Audio Engine...", total=100)
    task_browser = progress.add_task("[dim]Browser Visuals...", total=100)

    with Live(refresh_per_second=20, console=console, screen=True) as live:
        frame = 0
        while not stop_event.is_set():
            time.sleep(0.05)
            frame += 1
            
            # Progress Updates
            progress.update(task_overall, description=f"[bold green]{broker.message}")
            if broker.audio_tasks:
                progress.update(task_audio, completed=broker.audio_progress, description=f"[cyan]Audio Engine: {broker.audio_tasks[-1]}")
            if broker.timeline_tasks:
                progress.update(task_browser, completed=broker.timeline_progress, description=f"[cyan]Browser: {broker.timeline_tasks[-1]}")
                
            ascii_text = generate_rainbow_ascii(frame, flash=False)
            
            group = Group(
                Align.center(Panel(ascii_text, border_style="blue", title="[bold]ShowAI Execution Space", subtitle="Do Not Close Terminal")),
                Panel(progress, border_style="green", title="Execution Progress")
            )
            live.update(group)

def run_cli_ui(script_path):
    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found.")
        sys.exit(1)

    result_container = {"success": False, "error": None}
    
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    
    stop_event = threading.Event()
    anim_thread = threading.Thread(target=_animation_loop, args=(stop_event,), daemon=True)
    anim_thread.start()
    
    # Run user script on main thread to avoid CUDA/asyncio/Playwright thread deadlocks
    with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
        run_script_internal(script_path, result_container)
        
    stop_event.set()
    anim_thread.join()
    
    if result_container["error"]:
        print(result_container["error"], file=sys.stderr)
        out_val = captured_out.getvalue()
        if out_val:
            print("\n--- Standard Output ---")
            print(out_val)
        err_val = captured_err.getvalue()
        if err_val:
            print("--- Standard Error ---", file=sys.stderr)
            print(err_val, file=sys.stderr)
        sys.exit(result_container.get("code") or 1)
    else:
        out_val = captured_out.getvalue()
        if out_val:
            print("\n--- Execution Output ---")
            print(out_val)
        print("\033[1;32mShowAI run completed successfully.\033[0m")

def main():
    parser = argparse.ArgumentParser(description="ShowAI - Programmatic Generative Visual Timelines")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run", help="Run a ShowAI python execution sequence")
    run_parser.add_argument("script", help="Path to your python script (e.g. example.py)")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_cli_ui(args.script)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
