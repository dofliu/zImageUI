import argparse
import torch
import os
from diffusers import ZImagePipeline

def generate(prompt, output_path):
    # Cache path
    cache_path = r"D:\AI_Cache\HuggingFace"
    os.makedirs(cache_path, exist_ok=True)
    
    print(f"Loading model from/to: {cache_path}")
    
    # Load Model
    pipe = ZImagePipeline.from_pretrained(
        "Tongyi-MAI/Z-Image-Turbo",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        cache_dir=cache_path,
        use_safetensors=True,
    )
    
    # Move to GPU
    pipe.to("cuda")
    
    print(f"Generating with prompt: {prompt}")
    
    # Generate
    image = pipe(
        prompt=prompt,
        height=1024,
        width=1024,
        num_inference_steps=9,
        guidance_scale=0.0,
        generator=torch.Generator("cuda").manual_seed(42), 
    ).images[0]
    
    # Save
    image.save(output_path)
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    generate(args.prompt, args.output)
