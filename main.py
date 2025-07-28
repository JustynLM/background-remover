import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
import os
import math
from collections import deque

class SmartBackgroundRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Background Remover with AI-like Selection")
        self.root.geometry("1400x900")
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.display_image = None
        self.backup_image = None
        
        # Display scaling info
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Selection modes
        self.selection_mode = "none"  # "manual", "magic_wand", "smart_object"
        self.selection_points = []
        self.selection_lines = []
        self.magic_wand_tolerance = 30
        
        # Smart selection
        self.selection_mask = None
        
        # Background color
        self.bg_color = (255, 255, 255)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the enhanced UI with smart selection tools"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Smart Background Remover", 
                               font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel
        control_frame = ttk.LabelFrame(main_frame, text="Smart Tools", padding="15")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        control_frame.configure(width=300)
        
        # Upload section
        upload_label = ttk.Label(control_frame, text="📁 Load Image", font=("Arial", 14, "bold"))
        upload_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        upload_btn = ttk.Button(control_frame, text="📁 Upload Photo", 
                               command=self.upload_photo)
        upload_btn.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Smart Selection Tools
        smart_label = ttk.Label(control_frame, text="🎯 Smart Selection Tools", font=("Arial", 14, "bold"))
        smart_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        # Magic Wand Tool
        self.magic_wand_btn = ttk.Button(control_frame, text="🪄 Magic Wand (Click Multiple Areas)", 
                                        command=self.activate_magic_wand, state="disabled")
        self.magic_wand_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Magic wand mode toggle
        wand_mode_frame = ttk.Frame(control_frame)
        wand_mode_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.additive_mode = tk.BooleanVar(value=True)
        self.additive_check = ttk.Checkbutton(wand_mode_frame, text="✚ Add to selection", 
                                             variable=self.additive_mode)
        self.additive_check.pack(side=tk.LEFT)
        
        self.wand_reset_btn = ttk.Button(wand_mode_frame, text="🗑️", width=3,
                                        command=self.reset_wand_selection, state="disabled")
        self.wand_reset_btn.pack(side=tk.RIGHT)
        
        # Tolerance slider for magic wand
        tolerance_frame = ttk.Frame(control_frame)
        tolerance_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(tolerance_frame, text="Sensitivity:").pack(side=tk.LEFT)
        self.tolerance_var = tk.IntVar(value=30)
        tolerance_slider = ttk.Scale(tolerance_frame, from_=5, to=100, 
                                   variable=self.tolerance_var, orient=tk.HORIZONTAL)
        tolerance_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.tolerance_label = ttk.Label(tolerance_frame, text="30")
        self.tolerance_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Update tolerance display
        def update_tolerance(*args):
            self.magic_wand_tolerance = self.tolerance_var.get()
            self.tolerance_label.config(text=str(self.magic_wand_tolerance))
        self.tolerance_var.trace('w', update_tolerance)
        
        # Smart Object Detection
        self.smart_object_btn = ttk.Button(control_frame, text="🔍 Auto-Detect Main Object", 
                                          command=self.smart_object_detection, state="disabled")
        self.smart_object_btn.grid(row=6, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Edge Detection
        self.edge_detect_btn = ttk.Button(control_frame, text="📐 Smart Edge Selection", 
                                         command=self.smart_edge_selection, state="disabled")
        self.edge_detect_btn.grid(row=7, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Manual selection (backup)
        self.manual_btn = ttk.Button(control_frame, text="✏️ Manual Selection (Click Points)", 
                                    command=self.activate_manual_selection, state="disabled")
        self.manual_btn.grid(row=8, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Selection controls
        selection_control_frame = ttk.Frame(control_frame)
        selection_control_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.clear_btn = ttk.Button(selection_control_frame, text="🗑️ Clear", 
                                   command=self.clear_selection, state="disabled")
        self.clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.invert_btn = ttk.Button(selection_control_frame, text="🔄 Invert", 
                                    command=self.invert_selection, state="disabled")
        self.invert_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.apply_btn = ttk.Button(control_frame, text="✅ Apply Selection", 
                                   command=self.apply_selection, state="disabled")
        self.apply_btn.grid(row=10, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Separator
        ttk.Separator(control_frame, orient='horizontal').grid(row=11, column=0, columnspan=2,
                                                              sticky=(tk.W, tk.E), pady=15)
        
        # Background section
        bg_label = ttk.Label(control_frame, text="🎨 New Background", font=("Arial", 14, "bold"))
        bg_label.grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Quick color buttons
        color_frame = ttk.Frame(control_frame)
        color_frame.grid(row=13, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.white_btn = ttk.Button(color_frame, text="⚪", width=4,
                                   command=lambda: self.quick_color((255, 255, 255)), state="disabled")
        self.white_btn.pack(side=tk.LEFT, padx=2)
        
        self.black_btn = ttk.Button(color_frame, text="⚫", width=4,
                                   command=lambda: self.quick_color((0, 0, 0)), state="disabled")
        self.black_btn.pack(side=tk.LEFT, padx=2)
        
        self.red_btn = ttk.Button(color_frame, text="🔴", width=4,
                                 command=lambda: self.quick_color((255, 0, 0)), state="disabled")
        self.red_btn.pack(side=tk.LEFT, padx=2)
        
        self.blue_btn = ttk.Button(color_frame, text="🔵", width=4,
                                  command=lambda: self.quick_color((0, 100, 255)), state="disabled")
        self.blue_btn.pack(side=tk.LEFT, padx=2)
        
        self.green_btn = ttk.Button(color_frame, text="🟢", width=4,
                                   command=lambda: self.quick_color((0, 200, 0)), state="disabled")
        self.green_btn.pack(side=tk.LEFT, padx=2)
        
        self.transparent_btn = ttk.Button(control_frame, text="🔳 Keep Transparent", 
                                         command=self.make_transparent, state="disabled")
        self.transparent_btn.grid(row=14, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        self.custom_color_btn = ttk.Button(control_frame, text="🎨 Custom Color", 
                                          command=self.choose_custom_color, state="disabled")
        self.custom_color_btn.grid(row=15, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Color preview
        self.color_preview = tk.Frame(control_frame, width=60, height=30, 
                                     bg="white", relief="sunken", bd=2)
        self.color_preview.grid(row=16, column=0, columnspan=2, pady=10)
        
        # Separator
        ttk.Separator(control_frame, orient='horizontal').grid(row=17, column=0, columnspan=2,
                                                              sticky=(tk.W, tk.E), pady=15)
        
        # Actions
        actions_label = ttk.Label(control_frame, text="💾 Save Result", font=("Arial", 14, "bold"))
        actions_label.grid(row=18, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        action_frame = ttk.Frame(control_frame)
        action_frame.grid(row=19, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.undo_btn = ttk.Button(action_frame, text="↶ Undo", 
                                  command=self.undo, state="disabled")
        self.undo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.reset_btn = ttk.Button(action_frame, text="🔄 Reset", 
                                   command=self.reset, state="disabled")
        self.reset_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.save_btn = ttk.Button(control_frame, text="💾 Save Image", 
                                  command=self.save_image, state="disabled")
        self.save_btn.grid(row=20, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Status
        self.status_label = ttk.Label(control_frame, text="🚀 Ready! Upload an image to start using smart tools", 
                                     font=("Arial", 10), foreground="blue",
                                     wraplength=250, justify=tk.LEFT)
        self.status_label.grid(row=21, column=0, columnspan=2, pady=15)
        
        # Right panel - Image display
        image_frame = ttk.LabelFrame(main_frame, text="🖼️ Image Preview", padding="15")
        image_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas = tk.Canvas(image_frame, bg="lightgray", width=800, height=700)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add help text to canvas
        help_text = """🎯 Upload an image to start using smart selection tools!

🪄 Magic Wand: Click multiple areas (builds selection)
🔍 Auto-Detect: Find main objects automatically  
📐 Edge Selection: Smart boundary detection
✏️ Manual: Click points around object"""
        
        self.canvas.create_text(400, 350, text=help_text, 
                               font=("Arial", 14), fill="gray", justify=tk.CENTER)
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
        # Configure grid
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
    
    def upload_photo(self):
        """Upload and load a photo"""
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=file_types
        )
        
        if filename:
            self.load_image(filename)
    
    def load_image(self, filename):
        """Load an image file"""
        try:
            self.original_image = Image.open(filename)
            self.processed_image = self.original_image.copy()
            
            # Reset states
            self.reset_selection_state()
            
            self.display_image_on_canvas()
            
            # Enable all smart tools
            self.magic_wand_btn.config(state="normal")
            self.smart_object_btn.config(state="normal")
            self.edge_detect_btn.config(state="normal")
            self.manual_btn.config(state="normal")
            self.save_btn.config(state="normal")
            self.reset_btn.config(state="normal")
            
            self.status_label.config(text=f"✅ Loaded: {os.path.basename(filename)}\n\nTry the smart tools:\n🪄 Magic Wand - click multiple areas to build selection\n🔍 Auto-Detect - find main object\n📐 Edge Select - smart boundaries")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def reset_selection_state(self):
        """Reset all selection-related state"""
        self.selection_points = []
        self.selection_lines = []
        self.selection_mask = None
        self.backup_image = None
        self.selection_mode = "none"
        self.canvas.config(cursor="")
        
        # Reset button states
        self.clear_btn.config(state="disabled")
        self.invert_btn.config(state="disabled")
        self.apply_btn.config(state="disabled")
        self.undo_btn.config(state="disabled")
        self.wand_reset_btn.config(state="disabled")
        
        # Disable background options
        for btn in [self.white_btn, self.black_btn, self.red_btn, self.blue_btn, 
                   self.green_btn, self.transparent_btn, self.custom_color_btn]:
            btn.config(state="disabled")
    
    def reset_wand_selection(self):
        """Reset/clear magic wand selection only"""
        self.selection_mask = None
        self.canvas.delete("overlay")
        
        self.clear_btn.config(state="disabled")
        self.invert_btn.config(state="disabled")
        self.apply_btn.config(state="disabled")
        
        self.status_label.config(text="🗑️ Magic wand selection cleared! Click areas to start fresh.")
    
    def activate_magic_wand(self):
        """Activate magic wand selection mode"""
        self.selection_mode = "magic_wand"
        self.canvas.config(cursor="target")
        self.wand_reset_btn.config(state="normal")
        
        if self.additive_mode.get():
            self.status_label.config(text="🪄 Magic Wand active! ✚ ADDITIVE MODE\nClick multiple areas to build selection.\nUncheck 'Add to selection' for single-click mode.")
        else:
            self.status_label.config(text="🪄 Magic Wand active! Single-click mode.\nCheck 'Add to selection' to build up selection.")
    
    def activate_manual_selection(self):
        """Activate manual point selection mode"""
        self.selection_mode = "manual"
        self.canvas.config(cursor="crosshair")
        self.selection_points = []  # Clear any existing points
        
        # Clear visual elements
        for line_id in self.selection_lines:
            self.canvas.delete(line_id)
        self.selection_lines = []
        
        self.clear_btn.config(state="normal")
        self.status_label.config(text="✏️ Manual mode: Click points around the object you want to KEEP.\nClick at least 3 points to form a shape.\nDouble-click to apply selection quickly!")
    
    def magic_wand_selection(self, click_x, click_y):
        """Perform magic wand selection at clicked point with additive support"""
        try:
            # Convert canvas coordinates to image coordinates
            img_x = int((click_x - self.offset_x) / self.scale_factor)
            img_y = int((click_y - self.offset_y) / self.scale_factor)
            
            if not (0 <= img_x < self.processed_image.width and 0 <= img_y < self.processed_image.height):
                return
            
            # Get the target color
            target_color = self.processed_image.getpixel((img_x, img_y))
            if len(target_color) == 4:  # RGBA
                target_color = target_color[:3]  # Use only RGB
            
            # Create new mask for this selection
            new_mask = Image.new("L", self.processed_image.size, 0)
            self.flood_fill(new_mask, img_x, img_y, target_color, self.magic_wand_tolerance)
            
            # Combine with existing selection if in additive mode
            if self.additive_mode.get() and self.selection_mask:
                # Combine masks (OR operation)
                combined_mask = Image.new("L", self.processed_image.size, 0)
                existing_pixels = self.selection_mask.load()
                new_pixels = new_mask.load()
                combined_pixels = combined_mask.load()
                
                for y in range(self.processed_image.height):
                    for x in range(self.processed_image.width):
                        # If either mask has a pixel selected, select it in combined mask
                        combined_pixels[x, y] = max(existing_pixels[x, y], new_pixels[x, y])
                
                self.selection_mask = combined_mask
            else:
                # Replace existing selection
                self.selection_mask = new_mask
            
            self.visualize_selection()
            
            self.clear_btn.config(state="normal")
            self.invert_btn.config(state="normal")
            self.apply_btn.config(state="normal")
            
            # Count selected areas for user feedback
            mask_pixels = self.selection_mask.load()
            selected_count = sum(1 for y in range(self.processed_image.height) 
                               for x in range(self.processed_image.width) 
                               if mask_pixels[x, y] > 0)
            
            if self.additive_mode.get():
                self.status_label.config(text=f"🪄 Magic wand added to selection!\nSelected: {selected_count:,} pixels\nKeep clicking to add more areas!")
            else:
                self.status_label.config(text=f"🪄 Magic wand selected {selected_count:,} pixels!\nTolerance: {self.magic_wand_tolerance}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Magic wand failed: {str(e)}")
    
    def flood_fill(self, mask, start_x, start_y, target_color, tolerance):
        """Flood fill algorithm for magic wand selection"""
        visited = set()
        queue = deque([(start_x, start_y)])
        
        img_pixels = self.processed_image.load()
        mask_pixels = mask.load()
        
        width, height = self.processed_image.size
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue
                
            visited.add((x, y))
            
            # Get current pixel color
            current_color = img_pixels[x, y]
            if len(current_color) == 4:  # RGBA
                current_color = current_color[:3]  # Use only RGB
            
            # Check if color is similar enough
            if self.color_distance(current_color, target_color) <= tolerance:
                mask_pixels[x, y] = 255  # Mark as selected
                
                # Add neighbors to queue
                queue.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    def color_distance(self, color1, color2):
        """Calculate color distance between two RGB colors"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))
    
    def smart_object_detection(self):
        """Automatically detect the main object in the image"""
        try:
            self.status_label.config(text="🔍 Analyzing image... Finding main object...")
            self.root.update()
            
            # Create a copy for processing
            img = self.processed_image.copy()
            if img.mode == "RGBA":
                img = img.convert("RGB")
            
            # Enhance contrast to help with detection
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Apply edge detection using PIL filters
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges = edges.filter(ImageFilter.MedianFilter(size=3))
            
            # Convert to grayscale for processing
            gray = edges.convert("L")
            
            # Find the center region (assume main object is somewhat centered)
            width, height = gray.size
            center_x, center_y = width // 2, height // 2
            
            # Create initial mask by finding connected regions from center
            mask = Image.new("L", gray.size, 0)
            
            # Use multiple seed points around the center
            seed_points = [
                (center_x, center_y),
                (center_x - width//6, center_y),
                (center_x + width//6, center_y),
                (center_x, center_y - height//6),
                (center_x, center_y + height//6)
            ]
            
            # For each seed point, select similar regions
            for seed_x, seed_y in seed_points:
                if 0 <= seed_x < width and 0 <= seed_y < height:
                    target_color = img.getpixel((seed_x, seed_y))
                    temp_mask = Image.new("L", img.size, 0)
                    self.flood_fill_rgb_image(temp_mask, img, seed_x, seed_y, target_color, 40)
                    
                    # Combine with main mask
                    mask_pixels = mask.load()
                    temp_pixels = temp_mask.load()
                    for y in range(height):
                        for x in range(width):
                            if temp_pixels[x, y] > 0:
                                mask_pixels[x, y] = 255
            
            # Clean up the mask
            mask = mask.filter(ImageFilter.MedianFilter(size=5))
            
            self.selection_mask = mask
            self.visualize_selection()
            
            self.clear_btn.config(state="normal")
            self.invert_btn.config(state="normal")
            self.apply_btn.config(state="normal")
            
            self.status_label.config(text="🔍 Auto-detection complete!\nCheck the selection and click Apply,\nor use Invert if background was selected.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Auto-detection failed: {str(e)}")
    
    def flood_fill_rgb_image(self, mask, img, start_x, start_y, target_color, tolerance):
        """Flood fill for RGB image"""
        visited = set()
        queue = deque([(start_x, start_y)])
        
        img_pixels = img.load()
        mask_pixels = mask.load()
        width, height = img.size
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue
                
            visited.add((x, y))
            
            current_color = img_pixels[x, y]
            
            if self.color_distance(current_color, target_color) <= tolerance:
                mask_pixels[x, y] = 255
                queue.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    def smart_edge_selection(self):
        """Smart edge-based selection"""
        try:
            self.status_label.config(text="📐 Finding smart edges...")
            self.root.update()
            
            img = self.processed_image.copy()
            if img.mode == "RGBA":
                img = img.convert("RGB")
            
            # Apply strong edge detection
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges = edges.filter(ImageFilter.SMOOTH_MORE)
            
            # Convert to grayscale and enhance
            gray = edges.convert("L")
            enhancer = ImageEnhance.Contrast(gray)
            gray = enhancer.enhance(3.0)
            
            # Create mask based on edge intensity
            mask = Image.new("L", gray.size, 0)
            gray_pixels = gray.load()
            mask_pixels = mask.load()
            
            width, height = gray.size
            threshold = 50  # Edge threshold
            
            # Find strong edges and fill connected regions
            for y in range(height):
                for x in range(width):
                    if gray_pixels[x, y] > threshold:
                        # This is an edge pixel, try to fill the region it bounds
                        self.fill_bounded_region(mask, x, y, width, height)
            
            # Clean up the mask
            mask = mask.filter(ImageFilter.MedianFilter(size=3))
            
            self.selection_mask = mask
            self.visualize_selection()
            
            self.clear_btn.config(state="normal")
            self.invert_btn.config(state="normal")
            self.apply_btn.config(state="normal")
            
            self.status_label.config(text="📐 Edge selection complete!\nReview the selection and click Apply.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Edge detection failed: {str(e)}")
    
    def fill_bounded_region(self, mask, x, y, width, height):
        """Fill a small region around edge pixels"""
        mask_pixels = mask.load()
        
        # Fill a small area around the edge
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    mask_pixels[nx, ny] = 255
    
    def visualize_selection(self):
        """Show the current selection on the canvas with improved visual feedback"""
        if not self.selection_mask:
            return
        
        # Create a visual overlay
        display_width = int(self.processed_image.width * self.scale_factor)
        display_height = int(self.processed_image.height * self.scale_factor)
        
        # Resize mask for display
        display_mask = self.selection_mask.resize((display_width, display_height), Image.Resampling.NEAREST)
        
        # Create overlay image with better visibility
        if self.selection_mode == "magic_wand" and self.additive_mode.get():
            # Use green for additive magic wand selections
            overlay = Image.new("RGBA", (display_width, display_height), (0, 255, 0, 120))
        else:
            # Use red for other selections
            overlay = Image.new("RGBA", (display_width, display_height), (255, 0, 0, 100))
        
        # Apply mask to overlay
        overlay_pixels = overlay.load()
        mask_pixels = display_mask.load()
        
        for y in range(display_height):
            for x in range(display_width):
                if mask_pixels[x, y] == 0:  # Not selected
                    overlay_pixels[x, y] = (0, 0, 0, 0)  # Transparent
        
        # Convert overlay to PhotoImage and display
        self.overlay_image = ImageTk.PhotoImage(overlay)
        
        # Clear existing overlay and add new one
        self.canvas.delete("overlay")
        self.canvas.create_image(self.offset_x + display_width//2, 
                                self.offset_y + display_height//2, 
                                image=self.overlay_image, tags="overlay")
    
    def invert_selection(self):
        """Invert the current selection"""
        if self.selection_mask:
            # Invert the mask
            mask_pixels = self.selection_mask.load()
            width, height = self.selection_mask.size
            
            for y in range(height):
                for x in range(width):
                    mask_pixels[x, y] = 255 - mask_pixels[x, y]
            
            self.visualize_selection()
            self.status_label.config(text="🔄 Selection inverted! Click Apply when ready.")
    
    def clear_selection(self):
        """Clear current selection"""
        self.selection_mask = None
        self.selection_points = []
        
        # Clear visual elements
        for line_id in self.selection_lines:
            self.canvas.delete(line_id)
        self.selection_lines = []
        
        # Clear any closing line
        if hasattr(self, 'closing_line_id'):
            self.canvas.delete(self.closing_line_id)
            delattr(self, 'closing_line_id')
        
        self.canvas.delete("overlay")
        
        self.clear_btn.config(state="disabled")
        self.invert_btn.config(state="disabled")
        self.apply_btn.config(state="disabled")
        
        # Update status based on current mode
        if self.selection_mode == "magic_wand":
            self.wand_reset_btn.config(state="normal")
            self.status_label.config(text="🗑️ Selection cleared. Magic wand still active - click areas to select!")
        elif self.selection_mode == "manual":
            self.status_label.config(text="🗑️ Manual selection cleared. Click points around the object you want to keep.")
        else:
            self.wand_reset_btn.config(state="disabled")
            self.status_label.config(text="🗑️ Selection cleared. Try a different smart tool!")
    
    def apply_selection(self):
        """Apply the current selection to remove background"""
        try:
            if not self.selection_mask and len(self.selection_points) < 3:
                messagebox.showwarning("Warning", "No selection to apply!\n\nFor manual selection: Click at least 3 points around the object you want to keep.\nFor smart tools: Use magic wand, auto-detect, or edge detection first.")
                return
            
            # Save current state for undo
            self.backup_image = self.processed_image.copy()
            
            # Create final mask
            if self.selection_mask:
                # Use smart selection mask
                final_mask = self.selection_mask
                print("Using smart selection mask")  # Debug
            else:
                # Use manual selection points
                print(f"Creating manual selection with {len(self.selection_points)} points")  # Debug
                final_mask = Image.new("L", self.processed_image.size, 0)
                img_points = []
                
                for i, (canvas_x, canvas_y) in enumerate(self.selection_points):
                    # Convert canvas coordinates to image coordinates
                    img_x = int((canvas_x - self.offset_x) / self.scale_factor)
                    img_y = int((canvas_y - self.offset_y) / self.scale_factor)
                    
                    # Clamp to image bounds
                    img_x = max(0, min(img_x, self.processed_image.width - 1))
                    img_y = max(0, min(img_y, self.processed_image.height - 1))
                    
                    img_points.append((img_x, img_y))
                    print(f"Point {i+1}: Canvas({canvas_x}, {canvas_y}) -> Image({img_x}, {img_y})")  # Debug
                
                print(f"Image size: {self.processed_image.size}")  # Debug
                print(f"Scale factor: {self.scale_factor}, Offset: ({self.offset_x}, {self.offset_y})")  # Debug
                
                # Create polygon mask
                if len(img_points) >= 3:
                    ImageDraw.Draw(final_mask).polygon(img_points, fill=255)
                    print("Polygon created successfully")  # Debug
                else:
                    messagebox.showwarning("Warning", "Need at least 3 points for manual selection!")
                    return
            
            # Apply mask to create transparency
            if self.processed_image.mode != "RGBA":
                self.processed_image = self.processed_image.convert("RGBA")
            
            # Apply transparency based on mask
            pixels = self.processed_image.load()
            mask_pixels = final_mask.load()
            
            pixels_removed = 0
            pixels_kept = 0
            
            for y in range(self.processed_image.height):
                for x in range(self.processed_image.width):
                    r, g, b, a = pixels[x, y]
                    if mask_pixels[x, y] == 0:  # Not selected (remove)
                        pixels[x, y] = (r, g, b, 0)  # Make transparent
                        pixels_removed += 1
                    else:
                        pixels_kept += 1
            
            print(f"Pixels removed: {pixels_removed:,}, Pixels kept: {pixels_kept:,}")  # Debug
            
            # Update UI
            self.selection_mode = "none"
            self.canvas.config(cursor="")
            self.canvas.delete("overlay")
            
            # Clear manual selection visuals
            for line_id in self.selection_lines:
                self.canvas.delete(line_id)
            self.selection_lines = []
            self.selection_points = []
            
            # Enable background options
            for btn in [self.white_btn, self.black_btn, self.red_btn, self.blue_btn, 
                       self.green_btn, self.transparent_btn, self.custom_color_btn]:
                btn.config(state="normal")
            
            self.undo_btn.config(state="normal")
            self.display_image_on_canvas()
            
            if pixels_removed > 0:
                self.status_label.config(text=f"🎉 Background removed successfully!\n{pixels_removed:,} pixels made transparent.\nChoose a new background color or save as PNG.")
            else:
                self.status_label.config(text="⚠️ No pixels were removed. Try:\n• Inverting the selection\n• Checking if you selected the object (not background)\n• Using a different selection tool")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply selection: {str(e)}")
            print(f"Apply selection error: {e}")  # Debug
    
    def on_canvas_double_click(self, event):
        """Handle double-click to complete manual selection"""
        if self.selection_mode == "manual" and len(self.selection_points) >= 3:
            self.apply_selection()
    
    def on_canvas_click(self, event):
        """Handle canvas clicks based on current mode"""
        if self.selection_mode == "magic_wand":
            self.magic_wand_selection(event.x, event.y)
        elif self.selection_mode == "manual":
            self.manual_selection_click(event)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag for manual selection"""
        # Only for manual mode - could add brush selection here
        pass
    
    def manual_selection_click(self, event):
        """Handle manual selection clicks"""
        if self.processed_image:
            self.selection_points.append((event.x, event.y))
            
            # Draw point with number label
            point_id = self.canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, 
                                              fill="red", outline="darkred", width=2)
            self.selection_lines.append(point_id)
            
            # Add point number
            text_id = self.canvas.create_text(event.x+10, event.y-10, text=str(len(self.selection_points)), 
                                            fill="red", font=("Arial", 12, "bold"))
            self.selection_lines.append(text_id)
            
            # Draw line to previous point
            if len(self.selection_points) > 1:
                prev_x, prev_y = self.selection_points[-2]
                line_id = self.canvas.create_line(prev_x, prev_y, event.x, event.y, 
                                                 fill="red", width=3)
                self.selection_lines.append(line_id)
            
            # Close polygon preview when we have 3+ points
            if len(self.selection_points) > 2:
                # Remove previous closing line if it exists
                if hasattr(self, 'closing_line_id'):
                    self.canvas.delete(self.closing_line_id)
                
                first_x, first_y = self.selection_points[0]
                self.closing_line_id = self.canvas.create_line(event.x, event.y, first_x, first_y, 
                                                              fill="red", width=2, dash=(10, 5))
                self.selection_lines.append(self.closing_line_id)
            
            # Enable controls when we have enough points
            if len(self.selection_points) >= 3:
                self.apply_btn.config(state="normal")
                self.invert_btn.config(state="normal")
                
                # Create preview of manual selection
                self.create_manual_selection_preview()
                
                self.status_label.config(text=f"✏️ {len(self.selection_points)} points selected.\nClick more points to refine or click Apply to use selection.")
            else:
                self.status_label.config(text=f"✏️ {len(self.selection_points)} point(s) selected.\nNeed at least 3 points to create a selection area.")
    
    def create_manual_selection_preview(self):
        """Create a preview of the manual selection"""
        if len(self.selection_points) < 3:
            return
        
        try:
            # Create a temporary mask for preview
            temp_mask = Image.new("L", self.processed_image.size, 0)
            img_points = []
            
            for canvas_x, canvas_y in self.selection_points:
                img_x = int((canvas_x - self.offset_x) / self.scale_factor)
                img_y = int((canvas_y - self.offset_y) / self.scale_factor)
                img_x = max(0, min(img_x, self.processed_image.width - 1))
                img_y = max(0, min(img_y, self.processed_image.height - 1))
                img_points.append((img_x, img_y))
            
            # Create polygon
            ImageDraw.Draw(temp_mask).polygon(img_points, fill=255)
            
            # Store for visualization
            self.selection_mask = temp_mask
            self.visualize_selection()
            
        except Exception as e:
            print(f"Preview creation failed: {e}")  # Debug
    
    def quick_color(self, color):
        """Apply a quick background color"""
        self.bg_color = color
        self.apply_background_color()
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        self.color_preview.config(bg=hex_color)
    
    def make_transparent(self):
        """Keep the image transparent"""
        if self.processed_image and self.processed_image.mode == "RGBA":
            self.status_label.config(text="✨ Image kept transparent! Save as PNG to preserve transparency.")
        else:
            messagebox.showinfo("Info", "Image is transparent! Save as PNG to keep transparency.")
    
    def choose_custom_color(self):
        """Choose a custom background color"""
        color = colorchooser.askcolor(color=self.bg_color, title="Choose Background Color")
        if color[0]:
            self.bg_color = tuple(int(c) for c in color[0])
            hex_color = color[1]
            self.color_preview.config(bg=hex_color)
            self.apply_background_color()
    
    def apply_background_color(self):
        """Apply the selected background color"""
        if not self.processed_image:
            return
        
        try:
            if self.backup_image is None:
                self.backup_image = self.processed_image.copy()
            
            if self.processed_image.mode == "RGBA":
                new_image = Image.new("RGB", self.processed_image.size, self.bg_color)
                new_image.paste(self.processed_image, mask=self.processed_image.split()[-1])
                self.processed_image = new_image
            
            self.undo_btn.config(state="normal")
            self.display_image_on_canvas()
            self.status_label.config(text=f"🎨 Background color applied! Save your result.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply background: {str(e)}")
    
    def undo(self):
        """Undo last action"""
        if self.backup_image:
            self.processed_image = self.backup_image.copy()
            self.backup_image = None
            self.undo_btn.config(state="disabled")
            self.display_image_on_canvas()
            self.status_label.config(text="⏪ Undone! Previous state restored.")
    
    def reset(self):
        """Reset to original image"""
        if self.original_image:
            self.processed_image = self.original_image.copy()
            self.reset_selection_state()
            self.display_image_on_canvas()
            self.status_label.config(text="🔄 Reset to original. Ready for smart selection!")
    
    def save_image(self):
        """Save the processed image"""
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image to save!")
            return
        
        if self.processed_image.mode == "RGBA":
            default_ext = ".png"
            file_types = [
                ("PNG files (keeps transparency)", "*.png"),
                ("JPEG files (solid background)", "*.jpg"),
            ]
        else:
            default_ext = ".jpg"
            file_types = [
                ("JPEG files", "*.jpg"),
                ("PNG files", "*.png"),
            ]
        
        filename = filedialog.asksaveasfilename(
            title="Save your smart-edited image",
            defaultextension=default_ext,
            filetypes=file_types
        )
        
        if filename:
            try:
                if filename.lower().endswith(('.jpg', '.jpeg')) and self.processed_image.mode == "RGBA":
                    rgb_image = Image.new("RGB", self.processed_image.size, (255, 255, 255))
                    rgb_image.paste(self.processed_image, mask=self.processed_image.split()[-1])
                    rgb_image.save(filename, quality=95)
                    messagebox.showinfo("Saved!", f"Image saved as JPEG:\n{os.path.basename(filename)}")
                else:
                    self.processed_image.save(filename)
                    messagebox.showinfo("Saved!", f"Image saved:\n{os.path.basename(filename)}")
                
                self.status_label.config(text=f"💾 Saved: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def display_image_on_canvas(self):
        """Display the current image on canvas"""
        if not self.processed_image:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Calculate display size
        canvas_width = 800
        canvas_height = 700
        img_width, img_height = self.processed_image.size
        
        # Scale to fit canvas while maintaining aspect ratio
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y)
        
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)
        
        # Calculate offset to center image
        self.offset_x = (canvas_width - display_width) // 2
        self.offset_y = (canvas_height - display_height) // 2
        
        # Resize image for display
        display_img = self.processed_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self.display_image = ImageTk.PhotoImage(display_img)
        
        # Display centered on canvas
        self.canvas.create_image(self.offset_x + display_width//2, 
                                self.offset_y + display_height//2, 
                                image=self.display_image)

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartBackgroundRemover(root)
    root.mainloop()