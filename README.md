# AI Career Agent

AI 求职助手 MVP — 面向大学生秋招春招的 AI 辅助工具

## 项目结构

```
AICareerAgent/
├── backend/
│   ├── app/
│   │   ├── agents/           # 5 个核心 Agent
│   │   │   ├── resume_agent.py              # PDF 解析 + 能力画像
│   │   │   ├── job_matching_agent.py        # Mock 岗位 + 匹配评分
│   │   │   ├── resume_optimizer_agent.py    # 简历优化建议
│   │   │   ├── interview_agent.py           # 模拟面试 + 反馈
│   │   │   ├── application_tracker_agent.py # 投递追踪
│   │   │   └── engine.py                    # 统一编排引擎
│   │   ├── api/              # FastAPI 路由
│   │   ├── core/             # 配置
│   │   ├── db/               # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   └── main.py           # FastAPI 入口
│   ├── tests/                # 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # API 客户端
│   │   ├── components/       # React 组件
│   │   ├── pages/            # 页面
│   │   ├── styles/           # 样式
│   │   └── utils/            # 工具函数
│   └── package.json
└── docs/
    ├── API.md                # API 文档
    └── TEST_PLAN.md          # 测试计划
```

## 快速启动

```bash
# 1. 启动 PostgreSQL
docker run --name postgres-career -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=aicareragent -p 5432:5432 -d postgres:16

# 2. 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 3. 前端（新终端）
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## MVP 功能清单

- [x] PDF 简历上传与解析
- [x] 能力画像生成
- [x] Mock 岗位库（5 个典型岗位）
- [x] 简历-JD 匹配评分
- [x] 简历优化建议
- [x] 模拟面试 + 反馈
- [x] 投递进度追踪
- [ ] 真实招聘网站对接（Phase 2）
- [ ] LLM 增强解析（Phase 2）
- [ ] 用户认证系统（Phase 2）
