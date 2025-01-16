import mido

# 手动设置 mido 使用 'rtmidi' 作为后端
mido.set_backend('mido.backends.rtmidi')

import keyboard  # 使用 keyboard 模块进行全局热键监听
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox  # 用于显示错误提示
import threading

# 初始化全局变量
midi_out = None
instances_config = []  # 存储用户配置的实例
current_notes = {}  # 当前音符计数器，用于每个实例的递增和循环
instance_listbox = None  # 用于显示实例的列表框

# 函数用于发送 MIDI 信号
def send_midi_signal(base_note, shortcut, max_notes, channel):
    global current_notes
    if midi_out:
        current_note = current_notes[shortcut]

        # 发送 MIDI note_on 信号，指定通道
        midi_out.send(mido.Message('note_on', note=current_note, velocity=100, channel=channel - 1))
        print(f'MIDI Note {current_note} ON sent for {shortcut} on channel {channel}.')

        # 设置计时器，1 秒后自动发送 note_off 信号
        threading.Timer(1.0, send_midi_signal_off, args=(current_note, shortcut, base_note, max_notes, channel)).start()

# 函数用于发送 MIDI note_off 信号并递增音符
def send_midi_signal_off(note, shortcut, base_note, max_notes, channel):
    if midi_out:
        midi_out.send(mido.Message('note_off', note=note, velocity=0, channel=channel - 1))
        print(f'MIDI Note {note} OFF sent for {shortcut} on channel {channel}.')

        # 递增当前音符编号并循环
        current_notes[shortcut] = base_note + (current_notes[shortcut] - base_note + 1) % max_notes

# 添加实例配置
def add_instance(shortcut, base_note, max_notes, channel):
    global instances_config, current_notes, instance_listbox
    config = {
        'shortcut': shortcut,
        'base_note': base_note,
        'max_notes': max_notes,
        'channel': channel
    }
    instances_config.append(config)
    current_notes[shortcut] = base_note  # 初始化当前音符计数器
    setup_instance(shortcut, base_note, max_notes, channel)
    
    # 更新列表框
    if instance_listbox:
        instance_listbox.insert(tk.END, f"{shortcut} | Base Note: {base_note} | Max Notes: {max_notes} | Channel: {channel}")

# 删除实例配置
def delete_instance():
    global instances_config, current_notes, instance_listbox
    selected_index = instance_listbox.curselection()
    if selected_index:
        index = selected_index[0]
        instance = instances_config.pop(index)
        shortcut = instance['shortcut']
        
        # 清除当前实例的键监听和全局记录
        current_notes.pop(shortcut, None)
        keyboard.remove_hotkey(shortcut)

        # 删除列表框中的选项
        instance_listbox.delete(index)
        print(f"Instance {shortcut} deleted.")
    else:
        messagebox.showwarning("Delete Instance", "Please select an instance to delete.")

# 编辑实例配置
def edit_instance():
    global instances_config, instance_listbox
    selected_index = instance_listbox.curselection()
    if selected_index:
        index = selected_index[0]
        instance = instances_config[index]

        # 弹出编辑窗口
        edit_window = tk.Toplevel()
        edit_window.title("Edit Instance")
        edit_window.geometry("300x300")
        edit_window.configure(bg="#1e1e1e")

        # 设置样式
        style = ttk.Style()
        style.configure("TLabel", foreground="#ffffff", background="#1e1e1e", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("Custom.TButton", foreground="#000000", background="#cccccc", font=("Segoe UI", 10))

        # 输入框用于编辑实例
        ttk.Label(edit_window, text="Shortcut:").pack(pady=5)
        shortcut_entry = ttk.Entry(edit_window)
        shortcut_entry.insert(0, instance['shortcut'])
        shortcut_entry.pack(pady=5)

        ttk.Label(edit_window, text="Base Note:").pack(pady=5)
        base_note_entry = ttk.Entry(edit_window)
        base_note_entry.insert(0, instance['base_note'])
        base_note_entry.pack(pady=5)

        ttk.Label(edit_window, text="Max Notes:").pack(pady=5)
        max_notes_entry = ttk.Entry(edit_window)
        max_notes_entry.insert(0, instance['max_notes'])
        max_notes_entry.pack(pady=5)

        ttk.Label(edit_window, text="Channel:").pack(pady=5)
        channel_entry = ttk.Entry(edit_window)
        channel_entry.insert(0, instance['channel'])
        channel_entry.pack(pady=5)

        def save_changes():
            try:
                new_shortcut = shortcut_entry.get()
                new_base_note = int(base_note_entry.get())
                new_max_notes = int(max_notes_entry.get())
                new_channel = int(channel_entry.get())

                # 输入验证
                if not new_shortcut or len(new_shortcut) < 2:
                    messagebox.showerror("Input Error", "Invalid shortcut. Please enter a valid shortcut.")
                    return
                if new_base_note < 0 or new_base_note > 127:
                    messagebox.showerror("Input Error", "Base Note must be between 0 and 127.")
                    return
                if new_max_notes <= 0:
                    messagebox.showerror("Input Error", "Max Notes must be a positive integer.")
                    return
                if new_channel < 1 or new_channel > 16:
                    messagebox.showerror("Input Error", "Channel must be between 1 and 16.")
                    return

                # 更新实例配置
                keyboard.remove_hotkey(instance['shortcut'])
                instances_config[index] = {
                    'shortcut': new_shortcut,
                    'base_note': new_base_note,
                    'max_notes': new_max_notes,
                    'channel': new_channel
                }
                current_notes[new_shortcut] = new_base_note
                setup_instance(new_shortcut, new_base_note, new_max_notes, new_channel)
                instance_listbox.delete(index)
                instance_listbox.insert(index, f"{new_shortcut} | Base Note: {new_base_note} | Max Notes: {new_max_notes} | Channel: {new_channel}")
                print(f"Instance {new_shortcut} edited.")
                edit_window.destroy()
            except ValueError:
                messagebox.showerror("Input Error", "Invalid input. Please enter valid numbers for base note, max notes, and channel.")

        ttk.Button(edit_window, text="Save Changes", style="Custom.TButton", command=save_changes).pack(pady=10)

# 创建 GUI 窗口
def create_gui():
    global midi_out, instance_listbox

    # 创建窗口
    window = tk.Tk()
    window.title("Simple SW")
    window.geometry("800x600")
    window.configure(bg="#1e1e1e")

    # 设置样式
    style = ttk.Style()
    style.configure("TLabel", foreground="#ffffff", background="#1e1e1e", font=("Segoe UI", 10))
    style.configure("TEntry", font=("Segoe UI", 10))
    style.configure("Custom.TButton", foreground="#000000", background="#cccccc", font=("Segoe UI", 10))
    style.configure("TListbox", background="#333333", foreground="#ffffff", font=("Segoe UI", 10))

    # 创建下拉菜单标签
    ttk.Label(window, text="Select MIDI Port:").pack(pady=5)

    # 获取 MIDI 端口列表
    midi_ports = mido.get_output_names()

    # 下拉菜单用于选择 MIDI 端口
    selected_port = tk.StringVar(window)
    midi_menu = ttk.Combobox(window, textvariable=selected_port, values=midi_ports, state="readonly")
    midi_menu.pack(pady=5)

    # 按钮用于确认选择的 MIDI 端口
    def select_midi_port():
        global midi_out
        port_name = selected_port.get()
        if port_name:
            midi_out = mido.open_output(port_name)
            messagebox.showinfo("MIDI Port Selected", f"Selected MIDI Port: {port_name}")

    ttk.Button(window, text="Select", style="Custom.TButton", command=select_midi_port).pack(pady=5)

    # 实例列表框
    instance_listbox = tk.Listbox(window, height=10, width=80, bg="#333333", fg="#ffffff", font=("Segoe UI", 10))
    instance_listbox.pack(pady=10)

    ttk.Button(window, text="Delete Instance", style="Custom.TButton", command=delete_instance).pack(pady=5)
    ttk.Button(window, text="Edit Instance", style="Custom.TButton", command=edit_instance).pack(pady=5)

    # 初始化默认实例
    default_instances = [
        {"shortcut": "shift+alt+j", "base_note": 10, "max_notes": 10, "channel": 1},
        {"shortcut": "shift+alt+k", "base_note": 20, "max_notes": 10, "channel": 1},
        {"shortcut": "shift+alt+l", "base_note": 40, "max_notes": 10, "channel": 1},
        {"shortcut": "shift+alt+m", "base_note": 60, "max_notes": 10, "channel": 1},
        {"shortcut": "shift+alt+n", "base_note": 80, "max_notes": 10, "channel": 1},
    ]

    for instance in default_instances:
        add_instance(instance['shortcut'], instance['base_note'], instance['max_notes'], instance['channel'])

    # 运行主循环
    window.mainloop()

# 函数用于设置每个实例的快捷键监听
def setup_instance(shortcut, base_note, max_notes, channel):
    keyboard.add_hotkey(shortcut, lambda: send_midi_signal(base_note, shortcut, max_notes, channel))
    print(f"Listening for {shortcut} to send MIDI notes starting from {base_note} looping over {max_notes} notes on channel {channel}.")

# 启动 GUI
create_gui()
