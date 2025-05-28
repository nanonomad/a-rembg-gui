"""Model configuration and definitions for rembg GUI."""

MODELS = {
    "u2net": {
        "description": "General use (default)",
        "detailed_info": """
A robust general-purpose model suitable for most background removal tasks.

Strengths:
• Excellent balance of accuracy and speed
• Works well with objects, people, animals
• Good edge detection and fine detail preservation
• Reliable for production use

Best For:
• Product photography
• General object isolation
• Mixed content processing
• First-time users

Size: ~176MB | Speed: Medium | Quality: High
        """.strip(),
        "files": [("u2net.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx")]
    },
    "u2netp": {
        "description": "Lightweight version",
        "detailed_info": """
A lightweight version of u2net optimized for faster processing.

Strengths:
• Faster processing than u2net
• Lower memory requirements
• Good for batch processing
• Maintains decent accuracy

Weaknesses:
• Slightly reduced accuracy vs u2net
• May struggle with complex edges

Best For:
• Real-time applications
• Resource-constrained environments  
• Quick previews
• Large batch processing

Size: ~176MB | Speed: Fast | Quality: Good
        """.strip(),
        "files": [("u2netp.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx")]
    },
    "u2net_human_seg": {
        "description": "Human segmentation",
        "detailed_info": """
Specialized model optimized specifically for human segmentation.

Strengths:
• Superior accuracy for people/portraits
• Excellent hair detail preservation
• Handles complex poses well
• Good with partial occlusion

Weaknesses:
• Poor performance on non-human subjects
• May ignore objects/animals

Best For:
• Portrait photography
• Fashion/beauty images
• Human-centric content
• Professional headshots

Size: ~176MB | Speed: Medium | Quality: Excellent (humans)
        """.strip(),
        "files": [("u2net_human_seg.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx")]
    },
    "u2net_cloth_seg": {
        "description": "Clothing segmentation",
        "detailed_info": """
Specialized for clothing segmentation and fashion applications.

Strengths:
• Precise clothing boundary detection
• Separates upper/lower/full body clothing
• Excellent for fashion imagery
• Good fabric texture preservation

Categories:
• Upper body clothing
• Lower body clothing  
• Full body garments

Best For:
• Fashion e-commerce
• Virtual try-on applications
• Clothing design
• Apparel photography

Size: ~176MB | Speed: Medium | Quality: Excellent (clothing)
        """.strip(),
        "files": [("u2net_cloth_seg.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_cloth_seg.onnx")]
    },
    "silueta": {
        "description": "Compact general use (43MB)",
        "detailed_info": """
A compact version of u2net with significantly reduced file size.

Strengths:
• Very small model size (43MB)
• Fast download and loading
• Good general-purpose performance
• Low memory footprint

Weaknesses:
• Reduced accuracy vs full u2net
• May struggle with fine details
• Limited complex scene handling

Best For:
• Mobile applications
• Limited bandwidth environments
• Quick prototyping
• Edge computing devices

Size: 43MB | Speed: Very Fast | Quality: Good
        """.strip(),
        "files": [("silueta.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/silueta.onnx")]
    },
    "isnet-general-use": {
        "description": "General use (improved)",
        "detailed_info": """
Newer generation model with improved accuracy over u2net.

Strengths:
• Higher accuracy than u2net
• Better edge preservation
• Improved fine detail handling
• Modern architecture

Weaknesses:
• Larger computational requirements
• Slower than u2net variants

Best For:
• High-quality production work
• Complex scenes with fine details
• Professional applications
• When accuracy is paramount

Size: ~176MB | Speed: Slow | Quality: Excellent
        """.strip(),
        "files": [("isnet-general-use.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx")]
    },
    "isnet-anime": {
        "description": "Anime characters",
        "detailed_info": """
Specialized model trained specifically for anime and cartoon characters.

Strengths:
• Excellent for anime/manga imagery
• Handles stylized art well
• Good with cartoon characters
• Preserves artistic style details

Weaknesses:
• Poor performance on real photos
• Limited to stylized content
• May over-segment realistic images

Best For:
• Anime artwork
• Cartoon illustrations
• Digital art/manga
• Stylized character designs

Size: ~176MB | Speed: Medium | Quality: Excellent (anime)
        """.strip(),
        "files": [("isnet-anime.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-anime.onnx")]
    },
    "sam": {
        "description": "Segment Anything Model",
        "detailed_info": """
Meta's Segment Anything Model - versatile for any segmentation task.

Strengths:
• Extremely versatile
• Can segment any object
• Interactive point/box prompts
• State-of-the-art technology

Features:
• Point-based prompts supported
• Bounding box prompts
• Multiple object detection
• Zero-shot segmentation

Best For:
• Interactive segmentation
• Multiple object isolation
• Research applications
• Advanced users

Size: ~375MB (2 files) | Speed: Slow | Quality: Excellent
        """.strip(),
        "files": [
            ("vit_b-encoder-quant.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/vit_b-encoder-quant.onnx"),
            ("vit_b-decoder-quant.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/vit_b-decoder-quant.onnx")
        ]
    },
    "birefnet-general": {
        "description": "BiRefNet general",
        "detailed_info": """
Latest generation BiRefNet model for general background removal.

Strengths:
• State-of-the-art accuracy
• Excellent fine detail preservation
• Superior edge quality
• Handles complex scenes well

Features:
• Advanced bilateral refinement
• Multi-scale processing
• Robust to various lighting

Best For:
• Professional photography
• High-end commercial work
• Complex background scenes
• Maximum quality requirements

Size: ~176MB | Speed: Slow | Quality: Excellent
        """.strip(),
        "files": [("BiRefNet-general-epoch_244.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx")]
    },
    "birefnet-general-lite": {
        "description": "BiRefNet lightweight",
        "detailed_info": """
Lightweight version of BiRefNet balancing speed and quality.

Strengths:
• Good BiRefNet quality
• Faster than full BiRefNet
• Lower resource requirements
• Modern architecture

Best For:
• Fast high-quality processing  
• Production environments
• Batch processing
• Good speed/quality balance

Size: ~176MB | Speed: Medium | Quality: Very Good
        """.strip(),
        "files": [("BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx")]
    },
    "birefnet-portrait": {
        "description": "Human portraits",
        "detailed_info": """
BiRefNet model specialized for human portrait segmentation.

Strengths:
• Exceptional portrait quality
• Superior hair detail preservation
• Excellent skin tone handling
• Professional portrait results

Features:
• Advanced hair segmentation
• Skin-aware processing
• Portrait-specific training

Best For:
• Professional portraits
• Beauty/fashion photography  
• Headshots and profiles
• High-end portrait work

Size: ~176MB | Speed: Medium | Quality: Excellent (portraits)
        """.strip(),
        "files": [("BiRefNet-portrait-epoch_150.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-portrait-epoch_150.onnx")]
    },
    "birefnet-dis": {
        "description": "Dichotomous segmentation",
        "detailed_info": """
Specialized for dichotomous (binary) image segmentation tasks.

Strengths:
• Precise binary segmentation
• Clean edge definition
• Good for simple foreground/background
• Reduced processing complexity

Best For:
• Simple object isolation
• Clean cutout requirements
• Binary mask generation
• Preprocessing for other tools

Size: ~176MB | Speed: Medium | Quality: Very Good
        """.strip(),
        "files": [("BiRefNet-DIS-epoch_590.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-DIS-epoch_590.onnx")]
    },
    "birefnet-hrsod": {
        "description": "High-res object detection",
        "detailed_info": """
Optimized for high-resolution salient object detection.

Strengths:
• Excellent for high-resolution images
• Superior detail preservation
• Good for large format images
• Professional quality output

Features:
• High-resolution processing
• Salient object focus
• Fine detail preservation

Best For:
• Large format photography
• High-resolution artwork
• Professional print work
• Detailed technical imagery

Size: ~176MB | Speed: Slow | Quality: Excellent (high-res)
        """.strip(),
        "files": [("BiRefNet-HRSOD_DHU-epoch_115.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-HRSOD_DHU-epoch_115.onnx")]
    },
    "birefnet-cod": {
        "description": "Concealed object detection",
        "detailed_info": """
Specialized for detecting and segmenting concealed/camouflaged objects.

Strengths:
• Detects hidden/camouflaged objects
• Good for complex backgrounds
• Handles blended subjects
• Advanced object recognition

Features:
• Camouflage detection
• Hidden object revelation
• Complex scene analysis

Best For:
• Wildlife photography
• Camouflaged subjects
• Complex natural scenes
• Challenging segmentation tasks

Size: ~176MB | Speed: Medium | Quality: Very Good (concealed)
        """.strip(),
        "files": [("BiRefNet-COD-epoch_125.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-COD-epoch_125.onnx")]
    },
    "birefnet-massive": {
        "description": "Massive dataset trained",
        "detailed_info": """
BiRefNet trained on massive datasets for maximum versatility.

Strengths:
• Trained on largest dataset
• Maximum versatility
• Handles diverse content well
• Best general-purpose BiRefNet

Features:
• Massive training data
• Broad content coverage
• Robust performance

Best For:
• Unknown/mixed content
• General production use
• Diverse image collections
• Maximum reliability

Size: ~176MB | Speed: Medium | Quality: Excellent (versatile)
        """.strip(),
        "files": [("BiRefNet-massive-TR_DIS5K_TR_TEs-epoch_420.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-massive-TR_DIS5K_TR_TEs-epoch_420.onnx")]
    }
}

# Advanced parameters information for different features
ADVANCED_PARAMETERS = {
    "alpha_matting": {
        "description": "Post-processing technique to improve edge quality and transparency",
        "tooltip": "Alpha matting refines edges by analyzing foreground/background boundaries, creating smoother transitions and better transparency. Useful for hair, fur, and fine details.",
        "parameters": {
            "alpha_matting_foreground_threshold": {
                "description": "Trimap foreground threshold (0-255)",
                "default": 240,
                "range": "10-255",
                "tooltip": "Lower values include more pixels as definite foreground. Decrease if foreground areas are missing."
            },
            "alpha_matting_background_threshold": {
                "description": "Trimap background threshold (0-255)", 
                "default": 10,
                "range": "0-50",
                "tooltip": "Higher values include more pixels as definite background. Increase if background areas aren't fully removed."
            },
            "alpha_matting_erode_size": {
                "description": "Erode size for trimap generation",
                "default": 10,
                "range": "1-50",
                "tooltip": "Controls the boundary region size between foreground/background. Larger values create smoother transitions."
            }
        },
        "example_json": '''{
    "alpha_matting_foreground_threshold": 240,
    "alpha_matting_background_threshold": 10,
    "alpha_matting_erode_size": 10
}'''
    },
    "post_processing": {
        "description": "Additional processing options for mask refinement",
        "parameters": {
            "post_process_mask": {
                "description": "Apply post-processing to the mask",
                "default": False,
                "tooltip": "Additional mask cleaning and refinement"
            }
        },
        "example_json": '''{
    "post_process_mask": true
}'''
    },
    "sam_specific": {
        "description": "Segment Anything Model specific parameters",
        "parameters": {
            "input_points": {
                "description": "List of [x, y] coordinates for point prompts",
                "tooltip": "Click points to guide segmentation. Format: [[x1, y1], [x2, y2]]"
            },
            "input_labels": {
                "description": "Labels for input points (1=foreground, 0=background)",
                "tooltip": "1 for foreground points, 0 for background points. Must match input_points length."
            }
        },
        "example_json": '''{
    "input_points": [[100, 150], [200, 300]],
    "input_labels": [1, 0]
}'''
    },
    "background_replacement": {
        "description": "Background color replacement options",
        "parameters": {
            "bgcolor": {
                "description": "Background color as RGBA tuple",
                "default": "(0, 0, 0, 0)",
                "tooltip": "Replace background with solid color. Format: (R, G, B, A)"
            }
        },
        "example_json": '''{
    "bgcolor": [255, 255, 255, 255]
}'''
    }
}

DEFAULT_MODEL = "u2net"
