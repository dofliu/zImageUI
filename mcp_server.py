"""
Z-Image-Turbo MCP Server
允許透過 Model Context Protocol (MCP) 呼叫 zImage 圖片生成服務。
使用標準 python mcp SDK。
"""
import asyncio
import os
import uuid
import datetime
import sys

# 確保可以匯入本地模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server

from services.model_service import get_model_service
import config

# 初始化 Server
server = Server("zImage")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出可用的工具"""
    return [
        types.Tool(
            name="get_status",
            description="檢查圖片生成模型目前是否已載入記憶體。回傳 'Ready' 或 'Not Loaded'。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="warmup",
            description="預熱模型，將其載入記憶體中。回傳 'Model Loaded'。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="generate_image",
            description="根據提示詞生成圖片，回傳本地檔案路徑。",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "圖片生成的文字提示 (英文效果較佳)"},
                    "width": {"type": "integer", "default": 512, "description": "圖片寬度"},
                    "height": {"type": "integer", "default": 512, "description": "圖片高度"},
                    "seed": {"type": "integer", "description": "亂數種子 (可選)"},
                    "negative_prompt": {"type": "string", "description": "負面提示詞 (可選)"}
                },
                "required": ["prompt"],
            },
        ),
    ]

# 增加 stdout 重導向 Context Manager
class RedirectStdoutToStderr:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """處理工具呼叫"""
    
    # 使用 Context Manager 確保工具執行期間的 print 不會干擾 stdio 通信
    with RedirectStdoutToStderr():
        if name == "get_status":
            service = get_model_service()
            status = "Ready" if service.pipe is not None else "Not Loaded"
            return [types.TextContent(type="text", text=status)]

        elif name == "warmup":
            service = get_model_service()
            service.initialize_model()
            return [types.TextContent(type="text", text="Model Loaded")]

        elif name == "generate_image":
            if not arguments:
                raise ValueError("Missing arguments")
                
            prompt = arguments.get("prompt")
            if not prompt:
                raise ValueError("Missing required argument: prompt")
                
            width = arguments.get("width", 512)
            height = arguments.get("height", 512)
            seed = arguments.get("seed")
            negative_prompt = arguments.get("negative_prompt")

            service = get_model_service()
            
            os.makedirs(config.OUTPUT_PATH, exist_ok=True)

            image, used_seed = service.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                negative_prompt=negative_prompt
            )

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"mcp_{timestamp}_{unique_id}.png"
            filepath = os.path.join(config.OUTPUT_PATH, filename)
            
            image.save(filepath)
            abs_path = os.path.abspath(filepath)
            print(f"MCP Generated: {abs_path}")
            
            return [types.TextContent(type="text", text=abs_path)]

        else:
            raise ValueError(f"Unknown tool: {name}")

async def main():
    # 使用 stdio 進行通信
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="zImage",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    print("啟動 zImage MCP Server (Stdio Mode)...", file=sys.stderr)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)
