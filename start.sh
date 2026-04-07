#!/bin/bash
echo "========================================"
echo "  多Agent智能求职助手 - 启动脚本"
echo "========================================"
echo ""

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "[INFO] 未检测到 backend/.env 文件，从示例文件复制..."
    cp backend/.env.example backend/.env
    echo "[WARN] 请编辑 backend/.env 文件，填入你的大模型API密钥！"
    echo ""
fi

# 启动后端
echo "[1/2] 启动后端服务 (FastAPI, port 8000)..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

sleep 3

# 启动前端
echo "[2/2] 启动前端服务 (Vite, port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "  启动完成！"
echo "  前端地址: http://localhost:5173"
echo "  后端地址: http://localhost:8000"
echo "  API文档:  http://localhost:8000/docs"
echo "========================================"

# 等待退出
wait
