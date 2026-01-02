import os
os.chdir(r"D:\AI_Cache\LLM_Models")

files = [
    "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf",
    "qwen2.5-7b-instruct-q5_k_m-00002-of-00002.gguf"
]

with open("qwen2.5-7b-instruct-q5_k_m.gguf", "wb") as outfile:
    for f in files:
        print(f"合併: {f}")
        with open(f, "rb") as infile:
            outfile.write(infile.read())
print("完成!")