#!/bin/bash
# AICareerAgent 启动脚本
set -e

echo "========================================"
echo "  AI Career Agent - 启动脚本"
echo "========================================"
echo ""

# 检查 PostgreSQL
if ! docker ps --format '{{.Names}}' | grep -q postgres-career; then
    echo "🐘 启动 PostgreSQL..."
    docker run --name postgres-career \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=aicareragent \
        -p 5432:5432 \
        -d postgres:16
    sleep 3
    echo "✅ PostgreSQL 已启动"
else
    echo "✅ PostgreSQL 已在运行"
fi

# 后端
echo ""
echo "🚀 启动后端服务..."
cd backend
source venv/bin/activate 2>/dev/null || true
pip install -q -r requirements.txt 2>/dev/null || true
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID)"

# 等待后端就绪
echo "⏳ 等待后端就绪..."
for i in $(seq 1 10); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端就绪"
        break
    fi
    sleep 1
done

# 初始化 Mock 数据
echo ""
echo "📦 初始化 Mock 岗位数据..."
curl -s -X POST http://localhost:8000/api/v1/jobs/seed > /dev/null
echo "✅ Mock 数据已初始化"

# 前端
echo ""
echo "🎨 启动前端服务..."
cd ../frontend
npm install --silent 2>/dev/null || true
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端已启动 (PID: $FRONTEND_PID)"

echo ""
echo "========================================"
echo "  ✅ AI Career Agent 启动完成！"
echo "========================================"
echo ""
echo "  后端: http://localhost:8000"
echo "  前端: http://localhost:3000"
echo "  API文档: docs/API.md"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo ""

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker stop postgres-career 2>/dev/null; exit" INT TERM
wait
