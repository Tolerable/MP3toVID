# MP3toVID

## Description
MP3toVID is a Python-based GUI tool for converting MP3 files into MP4 videos. The tool allows you to select an image and MP3 file, and combines them into a video with metadata, perfect for album art or simple video creation.

## Features
- Converts MP3 audio files into MP4 videos.
- Adds images and metadata (Title, Artist, Album, Genre, etc.) to the video.
- Generates images using AI based on a text prompt if no image is provided.
- Customizable aspect ratios for images (1:1 or 16:9).
- GUI built with `Tkinter`.
- Easily select files through the graphical interface.
- Automatically manages WORKING and FINISHED directories.

## Installation

1. Clone the repository:
   bash
   git clone https://github.com/Tolerable/MP3toVID.git
   

2. Install the required Python packages:
   bash
   pip install -r requirements.txt
   

## Usage

1. Run the `MP3toVID.py` script:
   bash
   python MP3toVID.py
   

2. Use the GUI to:
   - Select an image and an MP3 file.
   - Add metadata like Title, Artist, Album, and Genre.
   - Generate an album cover image using AI if you don't provide one.
   - Click "Create MP4" to generate the video.

3. The generated video will be saved in the `FINISHED` directory.

## Dependencies

- `moviepy` for video editing.
- `mutagen` for metadata editing.
- `Pillow` for image handling.
- `requests` for AI image generation.

Install dependencies by running:
bash
pip install -r requirements.txt


## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests!

## Acknowledgements

Thanks to all contributors and open-source projects that make this tool possible.
