8#!/usr/bin/env python3
"""
YAML Combiner GUI - A tool to combine multiple YAML files with custom ordering
Copyright (C) 2024-2025 CBRE Inc. All rights reserved.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yaml
from pathlib import Path
import threading


class YAMLCombinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YAML Combiner Tool")
        self.root.geometry("900x700")
        self.root.configure(bg='white')  # Set white background for main window
        
        # Current directory and files
        self.current_dir = os.getcwd()
        self.yaml_files = []
        self.selected_files = []
        self.combine_mode = tk.StringVar(value="manual")  # "manual" or "automatic"
        
        self.setup_ui()
        self.load_yaml_files()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Configure modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styling with rounded appearance
        style.configure('Rounded.TButton',
                       relief='flat',
                       borderwidth=1,
                       focuscolor='none',
                       background='#f8f9fa',
                       foreground='#333333',
                       padding=(10, 6))
        
        style.map('Rounded.TButton',
                 background=[('active', '#e9ecef'),
                           ('pressed', '#dee2e6')])
        
        # Configure accent button for main action
        style.configure('AccentRounded.TButton',
                       relief='flat',
                       borderwidth=1,
                       focuscolor='none',
                       background='#007bff',
                       foreground='white',
                       padding=(12, 8))
        
        style.map('AccentRounded.TButton',
                 background=[('active', '#0056b3'),
                           ('pressed', '#004085')])
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Directory selection
        dir_frame = ttk.LabelFrame(main_frame, text="Directory", padding="5")
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory, style='Rounded.TButton').grid(row=0, column=0, padx=(0, 5))
        self.dir_label = ttk.Label(dir_frame, text=self.current_dir, foreground="blue")
        self.dir_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Combine Mode Selection
        mode_frame = ttk.LabelFrame(main_frame, text="Combine Mode", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="Manual Selection", variable=self.combine_mode, 
                       value="manual", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Automatic Detection", variable=self.combine_mode, 
                       value="automatic", command=self.on_mode_change).pack(side=tk.LEFT)
        
        # Auto-detect button (only visible in automatic mode)
        self.auto_detect_button = ttk.Button(mode_frame, text="Auto-Detect Files", 
                                           command=self.auto_detect_files, style='Rounded.TButton')
        self.auto_detect_button.pack(side=tk.RIGHT)
        
        # Available files section
        files_frame = ttk.LabelFrame(main_frame, text="Available YAML Files", padding="5")
        files_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        
        # Files listbox with scrollbar
        listbox_frame = ttk.Frame(files_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.files_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, 
                                       bg='white', fg='black',
                                       selectbackground='#007bff',
                                       selectforeground='white',
                                       relief='flat', borderwidth=1,
                                       highlightthickness=0)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        files_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        files_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        # Buttons for file operations
        file_buttons_frame = ttk.Frame(files_frame)
        file_buttons_frame.grid(row=1, column=0, pady=(5, 0))
        
        ttk.Button(file_buttons_frame, text="Add to Selection", command=self.add_to_selection, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Preview", command=self.preview_file, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Refresh", command=self.load_yaml_files, style='Rounded.TButton').pack(side=tk.LEFT)
        
        # Selected files and ordering section
        self.selection_frame = ttk.LabelFrame(main_frame, text="Selected Files (Drag to Reorder)", padding="5")
        self.selection_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 10))
        self.selection_frame.columnconfigure(0, weight=1)
        self.selection_frame.rowconfigure(0, weight=1)
        
        # Selected files listbox
        selection_listbox_frame = ttk.Frame(self.selection_frame)
        selection_listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        selection_listbox_frame.columnconfigure(0, weight=1)
        selection_listbox_frame.rowconfigure(0, weight=1)
        
        self.selection_listbox = tk.Listbox(
            selection_listbox_frame, 
            selectmode=tk.SINGLE,
            bg='white',  # Clean white background
            fg='black',  # Black text
            selectbackground='#007bff',  # Blue selection background
            selectforeground='white',  # White text when selected
            relief='flat',
            borderwidth=1,
            highlightthickness=0
        )
        self.selection_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        selection_scrollbar = ttk.Scrollbar(selection_listbox_frame, orient=tk.VERTICAL, command=self.selection_listbox.yview)
        selection_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.selection_listbox.configure(yscrollcommand=selection_scrollbar.set)
        
        # Bind drag and drop events
        self.selection_listbox.bind('<Button-1>', self.on_select_start)
        self.selection_listbox.bind('<B1-Motion>', self.on_drag)
        self.selection_listbox.bind('<ButtonRelease-1>', self.on_drop)
        
        # Selection control buttons
        selection_buttons_frame = ttk.Frame(self.selection_frame)
        selection_buttons_frame.grid(row=1, column=0, pady=(5, 0))
        
        ttk.Button(selection_buttons_frame, text="Move Up", command=self.move_up, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_buttons_frame, text="Move Down", command=self.move_down, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_buttons_frame, text="Remove", command=self.remove_from_selection, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_buttons_frame, text="Clear All", command=self.clear_selection, style='Rounded.TButton').pack(side=tk.LEFT)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output Options", padding="5")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output file:").grid(row=0, column=0, padx=(0, 5))
        self.output_var = tk.StringVar(value="combined.yaml")
        ttk.Entry(output_frame, textvariable=self.output_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="Browse", command=self.browse_output, style='Rounded.TButton').grid(row=0, column=2)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(action_frame, text="Combine YAMLs", command=self.combine_yamls, style='AccentRounded.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Preview Combined", command=self.preview_combined, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Split Combined YAML", command=self.split_combined_yaml, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Exit", command=self.root.quit, style='Rounded.TButton').pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Variables for drag and drop
        self.drag_start_index = None
        
        # Initialize UI state
        self.on_mode_change()
        
    def on_mode_change(self):
        """Handle mode change between manual and automatic"""
        try:
            is_automatic = self.combine_mode.get() == "automatic"
            
            if hasattr(self, 'selection_frame'):  # Check if UI is initialized
                if is_automatic:
                    # Update frame title and disable manual controls
                    self.selection_frame.configure(text="Auto-Detected Files (Read-Only)")
                    # Disable manual selection controls but keep them visible
                    if hasattr(self, 'files_listbox') and hasattr(self, 'selection_listbox'):
                        for widget in [self.files_listbox, self.selection_listbox]:
                            widget.configure(state=tk.DISABLED)
                else:
                    # Enable manual selection controls
                    self.selection_frame.configure(text="Selected Files (Drag to Reorder)")
                    if hasattr(self, 'files_listbox') and hasattr(self, 'selection_listbox'):
                        for widget in [self.files_listbox, self.selection_listbox]:
                            widget.configure(state=tk.NORMAL)
        except Exception as e:
            # Silently handle any errors during initialization
            pass
    
    def auto_detect_files(self):
        """Automatically detect and order files for combining"""
        try:
            detected_files, skipped_files = self.detect_files_automatically()
            
            if detected_files:
                # Show summary popup before proceeding
                self.show_detection_summary(detected_files, skipped_files)
                
                self.selected_files = detected_files
                self.update_selection_listbox()
                self.update_file_colors()
                self.status_var.set(f"Auto-detected {len(detected_files)} files for combining")
            else:
                messagebox.showwarning("Warning", "No suitable files found for automatic combining")
                
        except Exception as e:
            messagebox.showerror("Error", f"Auto-detection failed: {str(e)}")
    
    def show_detection_summary(self, detected_files, skipped_files):
        """Show a popup window with the detection summary"""
        # Create summary window
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Auto-Detection Summary")
        summary_window.geometry("600x500")
        summary_window.transient(self.root)
        summary_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(summary_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="YAML File Detection Results", 
                               font=("TkDefaultFont", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Files to combine tab
        combine_frame = ttk.Frame(notebook)
        notebook.add(combine_frame, text=f"Files to Combine ({len(detected_files)})")
        
        # Create text widget for combined files
        combine_text_frame = ttk.Frame(combine_frame)
        combine_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        combine_text = scrolledtext.ScrolledText(combine_text_frame, wrap=tk.WORD, height=15)
        combine_text.pack(fill=tk.BOTH, expand=True)
        
        # Add content to combine tab
        if detected_files:
            combine_text.insert(tk.END, "Files will be combined in this order:\n\n")
            for i, file in enumerate(detected_files, 1):
                file_type = self.get_file_type_description(file)
                combine_text.insert(tk.END, f"{i}. {file}\n   └─ {file_type}\n\n")
        else:
            combine_text.insert(tk.END, "No files detected for combining.")
        
        combine_text.config(state=tk.DISABLED)
        
        # Skipped files tab
        skip_frame = ttk.Frame(notebook)
        notebook.add(skip_frame, text=f"Skipped Files ({len(skipped_files)})")
        
        # Create text widget for skipped files
        skip_text_frame = ttk.Frame(skip_frame)
        skip_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        skip_text = scrolledtext.ScrolledText(skip_text_frame, wrap=tk.WORD, height=15)
        skip_text.pack(fill=tk.BOTH, expand=True)
        
        # Add content to skip tab
        if skipped_files:
            skip_text.insert(tk.END, "Files that will be skipped:\n\n")
            for file, reason in skipped_files:
                skip_text.insert(tk.END, f"• {file}\n  Reason: {reason}\n\n")
        else:
            skip_text.insert(tk.END, "No files were skipped.")
        
        skip_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Proceed with Combine", 
                  command=lambda: self.proceed_with_combine(summary_window, detected_files), 
                  style='AccentRounded.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_detection(summary_window), 
                  style='Rounded.TButton').pack(side=tk.RIGHT)
        
        # Center the window
        summary_window.update_idletasks()
        x = (summary_window.winfo_screenwidth() // 2) - (summary_window.winfo_width() // 2)
        y = (summary_window.winfo_screenheight() // 2) - (summary_window.winfo_height() // 2)
        summary_window.geometry(f"+{x}+{y}")
    
    def proceed_with_combine(self, window, detected_files):
        """Proceed with combining after user confirmation"""
        window.destroy()
        self.selected_files = detected_files
        self.update_selection_listbox()
        self.update_file_colors()
        
        # Now proceed with the actual combining
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showwarning("Warning", "Please specify an output file")
            return
        
        try:
            # Generate combined content with '---' separators
            combined_content = self.generate_combined_content_with_separators()
            
            # Write to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            messagebox.showinfo("Success", f"Successfully combined {len(self.selected_files)} automatically detected YAML files into {output_file}")
            self.status_var.set(f"Combined {len(self.selected_files)} files into {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to combine YAML files: {str(e)}")
    
    def get_file_type_description(self, file_name):
        """Get a description of the file type based on its name"""
        file_lower = file_name.lower()
        
        if '-predicted' in file_lower:
            return "Predicted file (Priority 1)"
        elif file_lower.startswith('global'):
            return "Global configuration file (Priority 2)"
        else:
            # Check if file is referenced in global-fields.yaml
            referenced_files = self.get_referenced_files_from_global_fields()
            file_base_name = self.get_file_base_name(file_name)
            if file_base_name in referenced_files:
                return "Referenced YAML file (Priority 3)"
            else:
                return "Regular YAML file (Priority 3)"
    
    def cancel_detection(self, window):
        """Cancel the auto-detection process"""
        window.destroy()
        self.selected_files = []
        self.update_selection_listbox()
        self.update_file_colors()
        self.status_var.set("Auto-detection cancelled")
    
    def detect_files_automatically(self):
        """Detect files automatically based on the specified criteria"""
        detected_files = []
        skipped_files = []  # List of (filename, reason) tuples
        
        # Get all YAML files from current directory and predicted folder
        all_yaml_files = self.yaml_files.copy()
        
        # Check 'predicted' folder if it exists
        predicted_folder = os.path.join(self.current_dir, 'predicted')
        if os.path.exists(predicted_folder):
            try:
                for file in os.listdir(predicted_folder):
                    if file.lower().endswith(('.yaml', '.yml')):
                        predicted_file_path = os.path.join('predicted', file)
                        all_yaml_files.append(predicted_file_path)
            except PermissionError:
                skipped_files.append(('predicted folder', 'Permission denied'))
        
        # Find and parse global-fields.yaml to get referenced files
        referenced_files = self.get_referenced_files_from_global_fields()
        
        # 1. Find file with '-predicted' in name (first)
        predicted_files = []
        
        for file in all_yaml_files:
            if '-predicted' in file.lower():
                if self.has_valid_global_fields(file):
                    predicted_files.append(file)
                else:
                    skipped_files.append((file, 'Invalid YAML format or empty file'))
        
        # Add the first predicted file found
        if predicted_files:
            detected_files.append(predicted_files[0])
            # Mark other predicted files as skipped if multiple exist
            for pred_file in predicted_files[1:]:
                skipped_files.append((pred_file, 'Multiple predicted files found, using first one only'))
        
        # 2. Find files starting with 'global' (second group)
        global_files = []
        for file in all_yaml_files:
            if file.lower().startswith('global') and file not in detected_files:
                if self.has_valid_global_fields(file):
                    global_files.append(file)
                else:
                    skipped_files.append((file, 'Invalid YAML format or empty file'))
        
        global_files.sort()  # Sort alphabetically
        detected_files.extend(global_files)
        
        # 3. Add remaining YAML files that are referenced in global-fields.yaml
        remaining_files = []
        for file in all_yaml_files:
            if (file not in detected_files and 
                not file.lower().startswith('global') and 
                '-predicted' not in file.lower()):
                
                # Check if this file is referenced in global-fields.yaml
                file_base_name = self.get_file_base_name(file)
                if file_base_name in referenced_files:
                    if self.has_valid_global_fields(file):
                        remaining_files.append(file)
                    else:
                        skipped_files.append((file, 'Invalid YAML format or empty file'))
                else:
                    skipped_files.append((file, 'Not referenced in global-fields.yaml'))
        
        remaining_files.sort()  # Sort alphabetically
        detected_files.extend(remaining_files)
        
        # Add files that were completely ignored due to other criteria
        for file in all_yaml_files:
            if file not in detected_files and not any(skip_file[0] == file for skip_file in skipped_files):
                skipped_files.append((file, 'Did not match any criteria'))
        
        return detected_files, skipped_files
    
    def get_referenced_files_from_global_fields(self):
        """Parse global-fields.yaml to extract referenced file names"""
        referenced_files = set()
        
        # Try to find global-fields.yaml in current directory or predicted folder
        global_fields_paths = [
            os.path.join(self.current_dir, 'global-fields.yaml'),
            os.path.join(self.current_dir, 'predicted', 'global-fields.yaml')
        ]
        
        global_fields_content = None
        for path in global_fields_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        global_fields_content = f.read()
                    break
                except Exception:
                    continue
        
        if not global_fields_content:
            return referenced_files
        
        # Parse the content to find file references
        # Look for patterns like =en-us-completions-key-dates/self.Something
        import re
        pattern = r'=([a-zA-Z0-9\-_]+)/'
        matches = re.findall(pattern, global_fields_content)
        
        for match in matches:
            # Convert the reference to actual filename
            filename = f"{match}.yaml"
            referenced_files.add(filename)
        
        return referenced_files
    
    def get_file_base_name(self, file_path):
        """Get the base name of a file without directory and extension"""
        # Handle files in subdirectories
        if os.path.sep in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = file_path
        
        # Remove extension
        base_name = os.path.splitext(file_name)[0]
        return f"{base_name}.yaml"
    
    def has_valid_global_fields(self, file_name):
        """Check if YAML file has valid global fields"""
        try:
            # Handle files that might be in subdirectories (like predicted folder)
            if os.path.sep in file_name or '/' in file_name:
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = os.path.join(self.current_dir, file_name)
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            # Basic validation - file should be a dictionary and not empty
            if isinstance(content, dict) and content:
                return True
            
            return False
            
        except Exception:
            # If file can't be parsed or read, skip it
            return False
        
    def load_yaml_files(self):
        """Load YAML files from the current directory"""
        try:
            self.yaml_files = []
            
            # Check if directory exists and is accessible
            if not os.path.exists(self.current_dir):
                self.status_var.set("Directory not found")
                return
                
            for file in os.listdir(self.current_dir):
                if file.lower().endswith(('.yaml', '.yml')) and os.path.isfile(os.path.join(self.current_dir, file)):
                    self.yaml_files.append(file)
            
            self.yaml_files.sort()
            
            # Update the listbox
            self.files_listbox.delete(0, tk.END)
            for file in self.yaml_files:
                self.files_listbox.insert(tk.END, file)
            
            # Update file colors based on selection status
            self.update_file_colors()
            
            self.status_var.set(f"Found {len(self.yaml_files)} YAML files")
            
        except PermissionError:
            messagebox.showerror("Error", "Permission denied: Cannot access the selected directory")
            self.status_var.set("Permission denied")
        except FileNotFoundError:
            messagebox.showerror("Error", "Directory not found")
            self.status_var.set("Directory not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YAML files: {str(e)}")
            self.status_var.set("Error loading files")
    
    def update_file_colors(self):
        """Update the text colors of files in the available files list"""
        try:
            for i, file in enumerate(self.yaml_files):
                if i < self.files_listbox.size():  # Check if index is valid
                    if file in self.selected_files:
                        # Set green color for selected files
                        self.files_listbox.itemconfig(i, {'fg': 'green'})
                    else:
                        # Set default black color for unselected files
                        self.files_listbox.itemconfig(i, {'fg': 'black'})
        except Exception as e:
            # Silently handle any indexing errors
            pass
    
    def browse_directory(self):
        """Browse for a directory containing YAML files"""
        directory = filedialog.askdirectory(initialdir=self.current_dir)
        if directory:
            self.current_dir = directory
            self.dir_label.config(text=directory)
            self.load_yaml_files()
    
    def browse_output(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("YML files", "*.yml"), ("All files", "*.*")],
            initialdir=self.current_dir
        )
        if filename:
            self.output_var.set(filename)
    
    def add_to_selection(self):
        """Add selected file to the selection list"""
        selection = self.files_listbox.curselection()
        if selection:
            file_name = self.yaml_files[selection[0]]
            if file_name not in self.selected_files:
                self.selected_files.append(file_name)
                self.update_selection_listbox()
                self.update_file_colors()  # Update colors after adding
                self.status_var.set(f"Added {file_name} to selection")
            else:
                messagebox.showinfo("Info", f"{file_name} is already in the selection")
    
    def remove_from_selection(self):
        """Remove selected file from the selection list"""
        selection = self.selection_listbox.curselection()
        if selection:
            index = selection[0]
            removed_file = self.selected_files.pop(index)
            self.update_selection_listbox()
            self.update_file_colors()  # Update colors after removing
            self.status_var.set(f"Removed {removed_file} from selection")
    
    def clear_selection(self):
        """Clear all selected files"""
        self.selected_files.clear()
        self.update_selection_listbox()
        self.update_file_colors()  # Update colors after clearing
        self.status_var.set("Cleared all selections")
    
    def update_selection_listbox(self):
        """Update the selection listbox display"""
        self.selection_listbox.delete(0, tk.END)
        for i, file in enumerate(self.selected_files):
            self.selection_listbox.insert(tk.END, f"{i+1}. {file}")
    
    def move_up(self):
        """Move selected item up in the list"""
        selection = self.selection_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self.selected_files[index], self.selected_files[index-1] = self.selected_files[index-1], self.selected_files[index]
            self.update_selection_listbox()
            self.selection_listbox.selection_set(index-1)
    
    def move_down(self):
        """Move selected item down in the list"""
        selection = self.selection_listbox.curselection()
        if selection and selection[0] < len(self.selected_files) - 1:
            index = selection[0]
            self.selected_files[index], self.selected_files[index+1] = self.selected_files[index+1], self.selected_files[index]
            self.update_selection_listbox()
            self.selection_listbox.selection_set(index+1)
    
    def on_select_start(self, event):
        """Handle start of drag operation"""
        self.drag_start_index = self.selection_listbox.nearest(event.y)
    
    def on_drag(self, event):
        """Handle drag operation"""
        pass  # Visual feedback could be added here
    
    def on_drop(self, event):
        """Handle drop operation"""
        if self.drag_start_index is not None:
            drop_index = self.selection_listbox.nearest(event.y)
            if drop_index != self.drag_start_index and 0 <= drop_index < len(self.selected_files):
                # Move the item
                item = self.selected_files.pop(self.drag_start_index)
                self.selected_files.insert(drop_index, item)
                self.update_selection_listbox()
                self.selection_listbox.selection_set(drop_index)
        self.drag_start_index = None
    
    def preview_file(self):
        """Preview the selected YAML file"""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to preview")
            return
        
        file_name = self.yaml_files[selection[0]]
        file_path = os.path.join(self.current_dir, file_name)
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview: {file_name}")
        preview_window.geometry("800x600")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.NONE, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert(tk.END, content)
                text_widget.config(state=tk.DISABLED)
        except Exception as e:
            text_widget.insert(tk.END, f"Error reading file: {str(e)}")
            text_widget.config(state=tk.DISABLED)
    
    def preview_combined(self):
        """Preview the combined YAML content"""
        # For automatic mode, auto-detect files first if none selected
        if self.combine_mode.get() == "automatic" and not self.selected_files:
            try:
                detected_files, skipped_files = self.detect_files_automatically()
                if detected_files:
                    self.show_detection_summary(detected_files, skipped_files)
                    return  # Let user review the summary first
                else:
                    messagebox.showwarning("Warning", "No suitable files found for automatic combining")
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Auto-detection failed: {str(e)}")
                return
            
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select files to combine")
            return
        
        # Create preview window with file management
        self.show_advanced_preview()
    
    def show_advanced_preview(self):
        """Show advanced preview window with file ordering and skipping options"""
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Advanced Combined YAML Preview")
        preview_window.geometry("1200x800")
        preview_window.transient(self.root)
        
        # Main container
        main_container = ttk.Frame(preview_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create horizontal paned window
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - File management
        left_panel = ttk.LabelFrame(paned_window, text="File Order & Selection", padding="5")
        paned_window.add(left_panel, weight=1)
        
        # Right panel - Preview
        right_panel = ttk.LabelFrame(paned_window, text="Combined YAML Preview", padding="5")
        paned_window.add(right_panel, weight=2)
        
        # Setup left panel
        self.setup_file_management_panel(left_panel, preview_window)
        
        # Setup right panel
        self.setup_preview_panel(right_panel, preview_window)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Combine YAMLs", 
                  command=lambda: self.combine_from_preview(preview_window), 
                  style='AccentRounded.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Reset to Original", 
                  command=lambda: self.reset_preview_files(), 
                  style='Rounded.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Close", 
                  command=preview_window.destroy, 
                  style='Rounded.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        
        # Store reference to preview window elements
        self.preview_window = preview_window
        
        # Center the window
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (preview_window.winfo_width() // 2)
        y = (preview_window.winfo_screenheight() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
    
    def setup_file_management_panel(self, parent, preview_window):
        """Setup the file management panel"""
        # Files to include section
        include_frame = ttk.LabelFrame(parent, text="Files to Include", padding="5")
        include_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        include_frame.columnconfigure(0, weight=1)
        include_frame.rowconfigure(0, weight=1)
        
        # Include listbox with scrollbar
        include_listbox_frame = ttk.Frame(include_frame)
        include_listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        include_listbox_frame.columnconfigure(0, weight=1)
        include_listbox_frame.rowconfigure(0, weight=1)
        
        self.preview_include_listbox = tk.Listbox(
            include_listbox_frame,
            selectmode=tk.SINGLE,
            bg='white',
            fg='black',
            selectbackground='#007bff',
            selectforeground='white',
            relief='flat',
            borderwidth=1,
            highlightthickness=0
        )
        self.preview_include_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        include_scrollbar = ttk.Scrollbar(include_listbox_frame, orient=tk.VERTICAL, 
                                        command=self.preview_include_listbox.yview)
        include_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_include_listbox.configure(yscrollcommand=include_scrollbar.set)
        
        # Include control buttons
        include_buttons_frame = ttk.Frame(include_frame)
        include_buttons_frame.grid(row=1, column=0, pady=(5, 0))
        
        ttk.Button(include_buttons_frame, text="↑ Move Up", 
                  command=self.preview_move_up, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(include_buttons_frame, text="↓ Move Down", 
                  command=self.preview_move_down, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(include_buttons_frame, text="❌ Skip File", 
                  command=self.preview_skip_file, style='Rounded.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(include_buttons_frame, text="🔄 Refresh Preview", 
                  command=self.update_preview_content, style='Rounded.TButton').pack(side=tk.LEFT)
        
        # Files to skip section
        skip_frame = ttk.LabelFrame(parent, text="Skipped Files", padding="5")
        skip_frame.pack(fill=tk.BOTH, expand=True)
        skip_frame.columnconfigure(0, weight=1)
        skip_frame.rowconfigure(0, weight=1)
        
        # Skip listbox with scrollbar
        skip_listbox_frame = ttk.Frame(skip_frame)
        skip_listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        skip_listbox_frame.columnconfigure(0, weight=1)
        skip_listbox_frame.rowconfigure(0, weight=1)
        
        self.preview_skip_listbox = tk.Listbox(
            skip_listbox_frame,
            selectmode=tk.SINGLE,
            bg='#f8f9fa',
            fg='#6c757d',
            selectbackground='#dc3545',
            selectforeground='white',
            relief='flat',
            borderwidth=1,
            highlightthickness=0
        )
        self.preview_skip_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        skip_scrollbar = ttk.Scrollbar(skip_listbox_frame, orient=tk.VERTICAL, 
                                     command=self.preview_skip_listbox.yview)
        skip_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_skip_listbox.configure(yscrollcommand=skip_scrollbar.set)
        
        # Skip control buttons
        skip_buttons_frame = ttk.Frame(skip_frame)
        skip_buttons_frame.grid(row=1, column=0, pady=(5, 0))
        
        ttk.Button(skip_buttons_frame, text="✅ Include File", 
                  command=self.preview_include_file, style='Rounded.TButton').pack(side=tk.LEFT)
        
        # Initialize file lists
        self.preview_included_files = self.selected_files.copy()
        self.preview_skipped_files = []
        
        # Populate listboxes
        self.update_preview_listboxes()
    
    def setup_preview_panel(self, parent, preview_window):
        """Setup the preview panel"""
        # Create text widget with scrollbar
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.preview_text_widget = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.NONE, 
            font=("Consolas", 10),
            bg='white',
            fg='black'
        )
        self.preview_text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Update initial content
        self.update_preview_content()
    
    def update_preview_listboxes(self):
        """Update the preview listboxes"""
        # Update included files listbox
        self.preview_include_listbox.delete(0, tk.END)
        for i, file in enumerate(self.preview_included_files):
            self.preview_include_listbox.insert(tk.END, f"{i+1}. {file}")
        
        # Update skipped files listbox
        self.preview_skip_listbox.delete(0, tk.END)
        for file in self.preview_skipped_files:
            self.preview_skip_listbox.insert(tk.END, f"❌ {file}")
    
    def update_preview_content(self):
        """Update the preview content"""
        if not hasattr(self, 'preview_text_widget'):
            return
            
        try:
            # Clear current content
            self.preview_text_widget.config(state=tk.NORMAL)
            self.preview_text_widget.delete(1.0, tk.END)
            
            if not self.preview_included_files:
                self.preview_text_widget.insert(tk.END, "No files selected for combining.")
            else:
                # Generate combined content
                combined_content = self.generate_preview_combined_content()
                self.preview_text_widget.insert(tk.END, combined_content)
            
            self.preview_text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            self.preview_text_widget.config(state=tk.NORMAL)
            self.preview_text_widget.delete(1.0, tk.END)
            self.preview_text_widget.insert(tk.END, f"Error generating preview: {str(e)}")
            self.preview_text_widget.config(state=tk.DISABLED)
    
    def generate_preview_combined_content(self):
        """Generate combined content from preview included files"""
        combined_content = []
        
        for i, file_name in enumerate(self.preview_included_files):
            # Handle files that might be in subdirectories (like predicted folder)
            if os.path.sep in file_name or '/' in file_name:
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = os.path.join(self.current_dir, file_name)
            
            # Add separator (except for the first file)
            if i > 0:
                combined_content.append("---")
            
            # Add file header comment with filename
            combined_content.append(f"# file name: {file_name}")
            
            # Read and add file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    combined_content.append(content)
            except Exception as e:
                combined_content.append(f"# Error reading file: {str(e)}")
        
        return '\n'.join(combined_content)
    
    def preview_move_up(self):
        """Move selected file up in the preview list"""
        selection = self.preview_include_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            # Swap files
            self.preview_included_files[index], self.preview_included_files[index-1] = \
                self.preview_included_files[index-1], self.preview_included_files[index]
            
            self.update_preview_listboxes()
            self.preview_include_listbox.selection_set(index-1)
            self.update_preview_content()
    
    def preview_move_down(self):
        """Move selected file down in the preview list"""
        selection = self.preview_include_listbox.curselection()
        if selection and selection[0] < len(self.preview_included_files) - 1:
            index = selection[0]
            # Swap files
            self.preview_included_files[index], self.preview_included_files[index+1] = \
                self.preview_included_files[index+1], self.preview_included_files[index]
            
            self.update_preview_listboxes()
            self.preview_include_listbox.selection_set(index+1)
            self.update_preview_content()
    
    def preview_skip_file(self):
        """Move selected file from include to skip list"""
        selection = self.preview_include_listbox.curselection()
        if selection:
            index = selection[0]
            file_to_skip = self.preview_included_files.pop(index)
            self.preview_skipped_files.append(file_to_skip)
            
            self.update_preview_listboxes()
            self.update_preview_content()
    
    def preview_include_file(self):
        """Move selected file from skip to include list"""
        selection = self.preview_skip_listbox.curselection()
        if selection:
            index = selection[0]
            file_to_include = self.preview_skipped_files.pop(index)
            self.preview_included_files.append(file_to_include)
            
            self.update_preview_listboxes()
            self.update_preview_content()
    
    def reset_preview_files(self):
        """Reset preview files to original selection"""
        self.preview_included_files = self.selected_files.copy()
        self.preview_skipped_files = []
        self.update_preview_listboxes()
        self.update_preview_content()
    
    def combine_from_preview(self, preview_window):
        """Combine files based on preview selection"""
        if not self.preview_included_files:
            messagebox.showwarning("Warning", "No files selected for combining")
            return
        
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showwarning("Warning", "Please specify an output file")
            return
        
        try:
            # Use the preview file order and selection
            original_selected_files = self.selected_files
            self.selected_files = self.preview_included_files
            
            # Generate combined content
            combined_content = self.generate_combined_content_with_separators()
            
            # Write to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            # Restore original selection
            self.selected_files = original_selected_files
            
            # Close preview window
            preview_window.destroy()
            
            messagebox.showinfo("Success", f"Successfully combined {len(self.preview_included_files)} YAML files into {output_file}")
            self.status_var.set(f"Combined {len(self.preview_included_files)} files into {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to combine YAML files: {str(e)}")
    
    def generate_combined_content(self):
        """Generate the combined YAML content"""
        combined_content = []
        
        for i, file_name in enumerate(self.selected_files):
            file_path = os.path.join(self.current_dir, file_name)
            
            # Add separator (except for the first file)
            if i > 0:
                combined_content.append("---")
            
            # Read and add file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                combined_content.append(content)
        
        return '\n'.join(combined_content)
    
    def combine_yamls(self):
        """Combine the selected YAML files"""
        # For automatic mode, auto-detect files first if none selected
        if self.combine_mode.get() == "automatic" and not self.selected_files:
            try:
                detected_files, skipped_files = self.detect_files_automatically()
                if detected_files:
                    self.show_detection_summary(detected_files, skipped_files)
                    return  # Let user review the summary first
                else:
                    messagebox.showwarning("Warning", "No suitable files found for automatic combining")
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Auto-detection failed: {str(e)}")
                return
        
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select files to combine")
            return
        
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showwarning("Warning", "Please specify an output file")
            return
        
        try:
            # Generate combined content with '---' separators
            combined_content = self.generate_combined_content_with_separators()
            
            # Write to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            mode_text = "automatically detected" if self.combine_mode.get() == "automatic" else "manually selected"
            messagebox.showinfo("Success", f"Successfully combined {len(self.selected_files)} {mode_text} YAML files into {output_file}")
            self.status_var.set(f"Combined {len(self.selected_files)} files into {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to combine YAML files: {str(e)}")
    
    def generate_combined_content_with_separators(self):
        """Generate the combined YAML content with '---' separators"""
        combined_content = []
        
        for i, file_name in enumerate(self.selected_files):
            # Handle files that might be in subdirectories (like predicted folder)
            if os.path.sep in file_name or '/' in file_name:
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = os.path.join(self.current_dir, file_name)
            
            # Add separator (except for the first file)
            if i > 0:
                combined_content.append("---")
            
            # Add file header comment with filename
            combined_content.append(f"# file name: {file_name}")
            
            # Read and add file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                combined_content.append(content)
        
        return '\n'.join(combined_content)
    
    def split_combined_yaml(self):
        """Split a combined YAML file back into separate files"""
        # Ask user to select the combined YAML file
        combined_file = filedialog.askopenfilename(
            title="Select Combined YAML File to Split",
            filetypes=[("YAML files", "*.yaml"), ("YML files", "*.yml"), ("All files", "*.*")],
            initialdir=self.current_dir
        )
        
        if not combined_file:
            return  # User cancelled
        
        try:
            # Parse the combined file and extract individual files
            extracted_files, errors = self.parse_combined_yaml(combined_file)
            
            if not extracted_files and not errors:
                messagebox.showwarning("Warning", "No files found to split. The file may not be a properly formatted combined YAML.")
                return
            
            # Ask user to select output directory
            output_dir = filedialog.askdirectory(
                title="Select Directory to Save Split Files",
                initialdir=self.current_dir
            )
            
            if not output_dir:
                return  # User cancelled
            
            # Write the extracted files
            written_files = []
            write_errors = []
            
            for filename, content in extracted_files:
                try:
                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    written_files.append(filename)
                except Exception as e:
                    write_errors.append(f"{filename}: {str(e)}")
            
            # Show results summary
            self.show_split_results(written_files, write_errors, errors)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to split YAML file: {str(e)}")
    
    def parse_combined_yaml(self, file_path):
        """Parse a combined YAML file and extract individual files"""
        extracted_files = []  # List of (filename, content) tuples
        errors = []  # List of error messages
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by document separators
            sections = content.split('---')
            
            current_filename = None
            current_content_lines = []
            
            for i, section in enumerate(sections):
                lines = section.strip().split('\n')
                
                # Look for filename header in this section
                filename_found = False
                content_lines = []
                
                for line in lines:
                    if line.strip().startswith('# file name:'):
                        # Extract filename from the comment
                        try:
                            filename_part = line.strip()[12:].strip()  # Remove '# file name:'
                            if filename_part:
                                # Save previous file if exists
                                if current_filename and current_content_lines:
                                    file_content = '\n'.join(current_content_lines).strip()
                                    if file_content:
                                        extracted_files.append((current_filename, file_content))
                                
                                # Start new file
                                current_filename = filename_part
                                current_content_lines = []
                                filename_found = True
                            else:
                                errors.append(f"Empty filename found in section {i+1}")
                        except Exception as e:
                            errors.append(f"Error parsing filename in section {i+1}: {str(e)}")
                    else:
                        # This is content (not a filename header)
                        if line.strip():  # Skip empty lines at the beginning
                            content_lines.append(line)
                
                # Add content lines to current file
                if current_filename and content_lines:
                    current_content_lines.extend(content_lines)
            
            # Don't forget the last file
            if current_filename and current_content_lines:
                file_content = '\n'.join(current_content_lines).strip()
                if file_content:
                    extracted_files.append((current_filename, file_content))
            
            return extracted_files, errors
            
        except Exception as e:
            errors.append(f"Error reading combined file: {str(e)}")
            return [], errors
    
    def show_split_results(self, written_files, write_errors, parse_errors):
        """Show a summary of the split operation results"""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Split Results Summary")
        results_window.geometry("600x500")
        results_window.transient(self.root)
        results_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(results_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="YAML Split Operation Results", 
                               font=("TkDefaultFont", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Successfully split files tab
        success_frame = ttk.Frame(notebook)
        notebook.add(success_frame, text=f"Successfully Split ({len(written_files)})")
        
        # Create text widget for successful files
        success_text_frame = ttk.Frame(success_frame)
        success_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        success_text = scrolledtext.ScrolledText(success_text_frame, wrap=tk.WORD, height=15)
        success_text.pack(fill=tk.BOTH, expand=True)
        
        # Add content to success tab
        if written_files:
            success_text.insert(tk.END, "Successfully created the following files:\n\n")
            for i, filename in enumerate(written_files, 1):
                success_text.insert(tk.END, f"{i}. {filename}\n")
        else:
            success_text.insert(tk.END, "No files were successfully created.")
        
        success_text.config(state=tk.DISABLED)
        
        # Errors tab (combine write errors and parse errors)
        all_errors = write_errors + parse_errors
        error_frame = ttk.Frame(notebook)
        notebook.add(error_frame, text=f"Errors ({len(all_errors)})")
        
        # Create text widget for errors
        error_text_frame = ttk.Frame(error_frame)
        error_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        error_text = scrolledtext.ScrolledText(error_text_frame, wrap=tk.WORD, height=15)
        error_text.pack(fill=tk.BOTH, expand=True)
        
        # Add content to error tab
        if all_errors:
            error_text.insert(tk.END, "Errors encountered during split operation:\n\n")
            for i, error in enumerate(all_errors, 1):
                error_text.insert(tk.END, f"{i}. {error}\n\n")
        else:
            error_text.insert(tk.END, "No errors encountered.")
        
        error_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Close", command=results_window.destroy, 
                  style='Rounded.TButton').pack(side=tk.RIGHT)
        
        # Update status
        if written_files:
            self.status_var.set(f"Successfully split {len(written_files)} files")
        else:
            self.status_var.set("Split operation completed with errors")
        
        # Center the window
        results_window.update_idletasks()
        x = (results_window.winfo_screenwidth() // 2) - (results_window.winfo_width() // 2)
        y = (results_window.winfo_screenheight() // 2) - (results_window.winfo_height() // 2)
        results_window.geometry(f"+{x}+{y}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    app = YAMLCombinerGUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()