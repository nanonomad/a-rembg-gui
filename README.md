# A Simple GUI for the RemBG AI Background Removal Tool

A graphical interface for the powerful [rembg](https://github.com/danielgatis/rembg) background removal library. Process single images, batch directories, or entire videos with real-time preview and advanced AI models.
![screenshot](https://github.com/user-attachments/assets/5702e5cd-76d5-483c-b8c6-25667bd84f86)


## ✨ Features

### 🖼️ **Multiple Processing Modes**
- **Single Image Processing** - Remove backgrounds from individual photos
- **Batch Directory Processing** - Process hundreds of images at once with live preview
- **Video Processing** - Extract frames, remove backgrounds, and reassemble with custom backgrounds

### 🤖 **Advanced AI Models**
- **15+ Specialized Models** including U²-Net, BiRefNet, ISNet, and Segment Anything Model (SAM)
- **Human Portraits** - Specialized models for superior people segmentation
- **Anime/Cartoon** - Optimized for stylized artwork
- **Clothing Segmentation** - Perfect for fashion e-commerce
- **High-Resolution Processing** - Handle large format images with precision

### 🚀 **Performance & Hardware**
- **GPU Acceleration** - CUDA and ROCm support for lightning-fast processing
- **Memory Management** - Smart memory allocation with file size validation
- **Multi-threading** - Non-blocking UI with background processing
- **Progress Tracking** - Real-time progress bars and status updates

### 🎨 **Video Processing**
- **Frame Extraction** - Custom FPS control or native framerate
- **Background Replacement** - Green screen, blue screen, or custom RGB colors
- **Video Reassembly** - Automatic MP4 output with original timing
- **Batch Frame Processing** - Process thousands of frames efficiently

### 🛠️ **Advanced Options**
- **Alpha Matting** - Refined edge quality for hair and fine details
- **Custom Parameters** - JSON configuration for expert users
- **Output Formats** - PNG with transparency or mask-only output
- **Preview System** - Live before/after image comparison

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rembg-gui.git
   cd rembg-gui
   ```

2. **Install dependencies**
   ```bash
   # Install with GPU support (recommended)
   pip install "rembg[gpu,cli]" pillow opencv-python psutil numpy

   # Or CPU-only version
   pip install rembg pillow opencv-python psutil numpy
   ```

3. **Run the application**
   ```bash
   python main.py


## ⚙️ Advanced Configuration

### Alpha Matting Parameters
Improve edge quality with JSON parameters:
```json
{
    "alpha_matting_foreground_threshold": 240,
    "alpha_matting_background_threshold": 10,
    "alpha_matting_erode_size": 10
}
```

### SAM Interactive Prompts
Use point prompts with Segment Anything Model:
```json
{
    "input_points": [[100, 150], [200, 300]],
    "input_labels": [1, 0]
}
```

### Custom Background Colors
```json
{
    "bgcolor": [255, 255, 255, 255]
}
```


# 🙏 Acknowledgments

- [danielgatis/rembg](https://github.com/danielgatis/rembg) - The amazing AI background removal library
- [ONNX Runtime](https://onnxruntime.ai/) - High-performance ML inference
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python's GUI toolkit

