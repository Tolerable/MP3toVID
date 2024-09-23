import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from moviepy.editor import ImageClip, AudioFileClip
import webbrowser
import threading
import json
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image, ImageTk
import requests
from io import BytesIO
import random
import time
import psutil

class MP3ToMP4Converter:
    def __init__(self, master):
        self.master = master
        master.title("MP3 to MP4 Converter")
        master.geometry("490x890")

        # Persistent data file
        self.persistent_data_file = "mp3_to_mp4_paths.json"
        self.load_persistent_data()

        # Create working and finished directories
        self.working_dir = os.path.normpath(os.path.join(os.getcwd(), "WORKING"))
        self.finished_dir = os.path.normpath(os.path.join(os.getcwd(), "FINISHED"))
        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.finished_dir, exist_ok=True)

        # Main frame
        main_frame = ttk.Frame(master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # Preview frame
        self.preview_frame = ttk.Frame(main_frame, width=340, height=340, style="Preview.TFrame")
        self.preview_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.preview_frame.grid_propagate(False)
        self.image_preview = ttk.Label(self.preview_frame)
        self.image_preview.place(relx=0.5, rely=0.5, anchor="center")

        # Create a style for the preview frame
        style = ttk.Style()
        style.configure("Preview.TFrame", background="black")

        # Image settings
        image_settings_frame = ttk.LabelFrame(main_frame, text="Image Settings")
        image_settings_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.img_entry = ttk.Entry(image_settings_frame, width=40)
        self.img_entry.grid(row=0, column=0, padx=5, pady=5)
        self.img_path = self.persistent_data.get('img_path', '')  # Keep full path internally
        if self.img_path:
            self.img_entry.insert(0, os.path.basename(self.img_path))  # Show only filename
        ttk.Button(image_settings_frame, text="Select Image", command=self.select_image).grid(row=0, column=1, padx=5, pady=5)

        self.aspect_ratio = tk.StringVar(value="16:9")
        ttk.Label(image_settings_frame, text="Aspect Ratio:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        ttk.Combobox(image_settings_frame, textvariable=self.aspect_ratio, values=["1:1", "16:9"]).grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.enhance_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(image_settings_frame, text="Enhance prompt", variable=self.enhance_var).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='w')

        # Metadata frame (middle)
        metadata_frame = ttk.LabelFrame(main_frame, text="Metadata")
        metadata_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.metadata = {
            'Title': tk.StringVar(value=self.persistent_data.get('Title', '')),
            'Artist': tk.StringVar(value=self.persistent_data.get('Artist', '')),
            'Copyright': tk.StringVar(value=self.persistent_data.get('Copyright', '')),
            'Album': tk.StringVar(value=self.persistent_data.get('Album', '')),
            'Genre': tk.StringVar(value=self.persistent_data.get('Genre', ''))
        }

        for i, (key, var) in enumerate(self.metadata.items()):
            ttk.Label(metadata_frame, text=f"{key}:").grid(row=i, column=0, padx=5, pady=2, sticky='w')
            ttk.Entry(metadata_frame, textvariable=var, width=40).grid(row=i, column=1, padx=5, pady=2)

        # Input and output frame
        io_frame = ttk.Frame(main_frame)
        io_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(io_frame, text="Audio Path:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.audio_entry = ttk.Entry(io_frame, width=40)
        self.audio_entry.grid(row=0, column=1, padx=5, pady=5)
        self.audio_path = self.persistent_data.get('audio_path', '')  # Keep full path internally
        if self.audio_path:
            self.audio_entry.insert(0, os.path.basename(self.audio_path))  # Show only filename
        ttk.Button(io_frame, text="Select Audio", command=self.select_audio).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(io_frame, text="Output Video Path:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.output_entry = ttk.Entry(io_frame, width=40)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_path = self.persistent_data.get('output_path', '')  # Keep full path internally
        if self.output_path:
            self.output_entry.insert(0, os.path.basename(self.output_path))  # Show only filename
        ttk.Button(io_frame, text="📁", command=self.open_location).grid(row=1, column=2, padx=5, pady=5)

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        ttk.Button(control_frame, text="Create MP4", command=self.start_video_creation_thread).grid(row=0, column=0, padx=5, pady=5)
        self.play_button = ttk.Button(control_frame, text="Play in External Player", command=self.play_external, state=tk.DISABLED)
        self.play_button.grid(row=0, column=1, padx=5, pady=5)

        # Processing label
        self.processing_label = ttk.Label(main_frame, text="")
        self.processing_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        # Prompt input and generate button (bottom)
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        prompt_frame.columnconfigure(0, weight=1)

        self.prompt_text = tk.Text(prompt_frame, width=40, height=3, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=0, sticky="ew")
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text.yview)
        prompt_scrollbar.grid(row=0, column=1, sticky="ns")
        self.prompt_text.configure(yscrollcommand=prompt_scrollbar.set)

        ttk.Button(prompt_frame, text="Generate Image", command=self.generate_ai_image).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self.prompt_text.bind("<Return>", self.handle_prompt_input)
        self.prompt_text.bind("<Shift-Return>", lambda e: "break")

        # Load initial image if available
        if self.img_path and os.path.exists(self.img_path):
            self.load_image_preview(self.img_path)
        else:
            print(f"Initial image not found: {self.img_path}")
        self.cleanup()

    def cleanup(self):
        try:
            # Force garbage collection to release any file handles
            import gc
            gc.collect()
            
            # Explicitly close any open clips
            if hasattr(self, 'img_clip'):
                self.img_clip.close()
                del self.img_clip
            if hasattr(self, 'audio_clip'):
                self.audio_clip.close()
                del self.audio_clip
            
            # Clear any remaining files in the WORKING directory
            for filename in os.listdir(self.working_dir):
                file_path = os.path.join(self.working_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        except Exception as e:
            print(f"Cleanup error: {e}")
        
    def load_image_preview(self, img_path):
        try:
            image = Image.open(img_path)

            # Set the preview size to 2/3 of the current size
            preview_width, preview_height = 320, 320  # 480 * 2/3 ≈ 320

            # Calculate scaling factor
            img_width, img_height = image.size
            scale = min(preview_width / img_width, preview_height / img_height)

            # Resize image
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create a black background image with 10px border
            background = Image.new('RGB', (preview_width + 20, preview_height + 20), (0, 0, 0))

            # Calculate position to paste the image centered
            paste_x = (background.width - new_width) // 2
            paste_y = (background.height - new_height) // 2

            # Paste the resized image onto the black background
            background.paste(image, (paste_x, paste_y))

            photo = ImageTk.PhotoImage(background)
            self.image_preview.configure(image=photo)
            self.image_preview.image = photo  # Keep a reference
        except Exception as e:
            print(f"Failed to load image preview: {e}")
            self.image_preview.configure(image="")
            self.image_preview.image = None

    def handle_prompt_input(self, event):
        self.generate_ai_image()
        return "break"

    def select_image(self):
        img_dir = os.path.normpath(self.persistent_data.get('img_dir', os.getcwd()))
        img_path = filedialog.askopenfilename(title="Select Image", initialdir=img_dir, filetypes=[("PNG files", "*.png")])
        if img_path:
            img_path = os.path.normpath(img_path)  # Normalize path slashes
            self.img_path = img_path  # Store the full path internally
            self.img_entry.delete(0, tk.END)
            self.img_entry.insert(0, os.path.basename(img_path))  # Show only the filename
            self.persistent_data['img_dir'] = os.path.dirname(img_path)
            self.persistent_data['img_path'] = img_path
            self.save_persistent_data()
            self.load_image_preview(img_path)

    def generate_ai_image(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Required", "Please enter a prompt for image generation.")
            return

        aspect_ratio = self.aspect_ratio.get()
        width, height = (1024, 1024) if aspect_ratio == "1:1" else (1920, 1080)
        seed = random.randint(1, 999999999)  # 9-digit random number
        enhance = "true" if self.enhance_var.get() else "false"

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"generated_image_{timestamp}_{aspect_ratio.replace(':', '_')}.png"

        url = f"https://image.pollinations.ai/prompt/{prompt}?nologo=true&seed={seed}&enhance={enhance}&model=flux&nofeed=true&width={width}&height={height}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            filepath = self.save_generated_image(image, filename)
            self.load_image_preview(filepath)
            # messagebox.showinfo("Success", f"Image generated and saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate image: {str(e)}")

    def save_generated_image(self, image, filename):
        filepath = os.path.join(self.working_dir, filename)
        image.save(filepath, "PNG")
        self.img_path = filepath
        self.img_entry.delete(0, tk.END)
        self.img_entry.insert(0, filename)  # Show only the filename
        self.persistent_data['img_path'] = filepath
        self.save_persistent_data()
        return filepath

    def select_audio(self):
        audio_dir = os.path.normpath(self.persistent_data.get('audio_dir', os.getcwd()))
        audio_path = filedialog.askopenfilename(title="Select Audio", initialdir=audio_dir, filetypes=[("MP3 files", "*.mp3")])
        if audio_path:
            audio_path = os.path.normpath(audio_path)  # Normalize path slashes
            self.audio_path = audio_path  # Update the audio_path attribute
            self.audio_entry.delete(0, tk.END)
            self.audio_entry.insert(0, os.path.basename(audio_path))  # Show only the filename
            self.persistent_data['audio_dir'] = os.path.dirname(audio_path)
            self.persistent_data['audio_path'] = audio_path
            self.save_persistent_data()

    def start_video_creation_thread(self):
        threading.Thread(target=self.create_video).start()

    def create_video(self):
        img_path = self.img_path
        audio_path = self.audio_path

        if not img_path or not audio_path:
            messagebox.showwarning("Input Required", "Please select both an image and an audio file.")
            return

        try:
            # Generate unique filenames for working copies
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
            working_img_filename = f"working_image_{timestamp}.png"
            working_audio_filename = f"working_audio_{timestamp}.mp3"
            output_filename = f"{audio_basename}_{timestamp}.mp4"

            working_img_path = os.path.join(self.working_dir, working_img_filename)
            working_audio_path = os.path.join(self.working_dir, working_audio_filename)
            output_path = os.path.join(self.working_dir, output_filename)

            # Copy files to working directory with unique names
            shutil.copy2(img_path, working_img_path)
            shutil.copy2(audio_path, working_audio_path)

            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_filename)

            # Create video using a separate function to ensure proper resource management
            self.process_video(working_img_path, working_audio_path, output_path)

            # Apply metadata
            self.edit_mp4_metadata(
                filename=output_path,
                title=self.metadata['Title'].get(),
                artist=self.metadata['Artist'].get(),
                album=self.metadata['Album'].get(),
                artwork=working_img_path
            )

            # Move finished video to FINISHED directory
            finished_output_path = os.path.join(self.finished_dir, output_filename)
            shutil.move(output_path, finished_output_path)
            
            # Update the output entry with just the filename
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_filename)

            # Update current_video_path for playing
            self.current_video_path = finished_output_path

            # Enable the play button
            self.play_button.config(state=tk.NORMAL)

            messagebox.showinfo("Success", f"Video created successfully: {output_filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create video: {str(e)}")
        finally:
            # Cleanup temporary files
            for file in [working_img_path, working_audio_path]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Failed to remove temporary file {file}: {str(e)}")
            
            # Perform general cleanup
            self.cleanup()

    def process_video(self, img_path, audio_path, output_path):
        with ImageClip(img_path) as img_clip, AudioFileClip(audio_path) as audio_clip:
            video = img_clip.set_duration(audio_clip.duration).set_audio(audio_clip)
            video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        
    def play_external(self):
        if hasattr(self, 'current_video_path'):
            self.play_video(self.current_video_path)

    def play_video(self, path):
        try:
            webbrowser.open(f"file://{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {str(e)}")

    def open_location(self):
        output_filename = self.output_entry.get()
        if output_filename:
            # Construct the full path to the output file in the FINISHED directory
            full_output_path = os.path.join(self.finished_dir, output_filename)
            
            if os.path.exists(full_output_path):
                # Open the directory containing the file
                webbrowser.open(f"file://{os.path.dirname(full_output_path)}")
            else:
                # If the file doesn't exist in FINISHED, check the WORKING directory
                working_output_path = os.path.join(self.working_dir, output_filename)
                if os.path.exists(working_output_path):
                    webbrowser.open(f"file://{os.path.dirname(working_output_path)}")
                else:
                    messagebox.showerror("Error", f"Output file not found: {output_filename}")
        else:
            messagebox.showerror("Error", "No output file specified.")

        # Print debug information
        print(f"Output filename: {output_filename}")
        print(f"FINISHED directory: {self.finished_dir}")
        print(f"WORKING directory: {self.working_dir}")
        print(f"Full output path (FINISHED): {os.path.join(self.finished_dir, output_filename)}")
        print(f"Full output path (WORKING): {os.path.join(self.working_dir, output_filename)}")

    def load_persistent_data(self):
        if os.path.exists(self.persistent_data_file):
            with open(self.persistent_data_file, 'r') as file:
                self.persistent_data = json.load(file)
        else:
            self.persistent_data = {}

    def save_persistent_data(self):
        self.persistent_data.update({
            'Title': self.metadata['Title'].get(),
            'Artist': self.metadata['Artist'].get(),
            'Copyright': self.metadata['Copyright'].get(),
            'Album': self.metadata['Album'].get(),
            'Genre': self.metadata['Genre'].get()
        })
        with open(self.persistent_data_file, 'w') as file:
            json.dump(self.persistent_data, file, indent=4)

    def edit_mp4_metadata(self, filename, title=None, artist=None, album=None, artwork=None):
        try:
            video = MP4(filename)

            if title:
                video["\xa9nam"] = title  # Title
            if artist:
                video["\xa9ART"] = artist  # Artist
            if album:
                video["\xa9alb"] = album  # Album

            if artwork:
                with open(artwork, "rb") as f:
                    video["covr"] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_PNG)]

            video.save()
            print(f"Metadata successfully updated for {filename}")
        except Exception as e:
            print(f"Failed to edit metadata for MP4: {e}")
            messagebox.showerror("Error", f"Failed to edit metadata for MP4: {str(e)}")

# Create and run the Tkinter GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = MP3ToMP4Converter(root)
    root.mainloop()
