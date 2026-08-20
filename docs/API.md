# AI Career Agent - API 接口文档

## Base URL
```
http://localhost:8000
```

## Health Check
```
GET /health
```

---

## 1. Resume Agent — 简历解析

### 上传简历
```http
POST /api/v1/resume/upload?user_id={user_id}
Content-Type: multipart/form-data

file: <PDF文件>
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "user_001",
  "original_filename": "resume.pdf",
  "parsed_text": "...",
  "skills": [{"name": "Python", "level": "intermediate"}],
  "experience": [...],
  "education": [...],
  "summary": "浙江大学 计算机科学与技术 本科毕业生 | 拥有2段实习经历...",
  "strength_analysis": [...],
  "created_at": "2026-08-15T10:00:00Z"
}
```

### 查询画像
```http
GET /api/v1/resume/profiles/{profile_id}
```

### 列出用户画像
```http
GET /api/v1/resume/profiles?user_id={user_id}
```

---

## 2. Job Matching Agent — 岗位匹配

### 获取岗位列表
```http
GET /api/v1/jobs/?limit=20&offset=0
```

### 初始化 Mock 数据
```http
POST /api/v1/jobs/seed
```

### 获取岗位详情
```http
GET /api/v1/jobs/{job_id}
```

### 计算匹配度
```http
POST /api/v1/jobs/match?profile_id={profile_id}&job_id={job_id}
```

**Response:**
```json
{
  "job_id": "uuid",
  "job_title": "后端开发工程师（校招）",
  "company": "字节跳动",
  "overall_score": 78.5,
  "skill_match": 85.0,
  "experience_match": 72.0,
  "education_match": 70.0,
  "gaps": ["Kafka", "Docker"],
  "suggestions": ["建议学习/强化以下技能: Kafka, Docker"]
}
```

---

## 3. Resume Optimizer — 简历优化

### 生成优化建议
```http
POST /api/v1/applications/optimize
Body:
{
  "resume_profile_id": "uuid",
  "job_id": "uuid"
}
```

**Response:**
```json
{
  "resume_profile_id": "uuid",
  "job_id": "uuid",
  "optimized_summary": "浙江大学计算机科学与技术毕业生，专注于后端开发方向...",
  "optimized_skills": ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"],
  "suggested_edits": [
    {
      "section": "skills",
      "original": "当前技能列表",
      "suggestion": "建议补充: Kafka, Docker",
      "reason": "这些技能是岗位 JD 中明确要求的"
    }
  ],
  "improvement_score": 88.5
}
```

---

## 4. Interview Agent — 模拟面试

### 创建面试会话
```http
POST /api/v1/interview/sessions
Body:
{
  "user_id": "user_001",
  "job_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "user_001",
  "job_id": "uuid",
  "status": "scheduled",
  "questions": [
    {"question": "请介绍一下你印象最深的项目", "category": "behavioral", "difficulty": "easy"},
    {"question": "Redis 缓存穿透如何解决？", "category": "technical", "difficulty": "medium"}
  ],
  "started_at": "2026-08-15T10:00:00Z"
}
```

### 提交答案获取反馈
```http
POST /api/v1/interview/sessions/{session_id}/submit
Body:
[
  {"question_index": 0, "answer": "我在阿里巴巴实习期间..."},
  {"question_index": 1, "answer": "缓存穿透是指..."}
]
```

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "feedback": [
    {
      "question_index": 0,
      "score": 75.0,
      "strengths": ["回答内容较为详实", "能结合实践经验"],
      "improvements": ["建议补充量化成果"],
      "suggested_answer": "使用 STAR 法则..."
    }
  ],
  "overall_score": 75.0
}
```

---

## 5. Application Tracker — 投递追踪

### 创建投递记录
```http
POST /api/v1/applications/
Body:
{
  "user_id": "user_001",
  "job_id": "uuid",
  "resume_profile_id": "uuid"
}
```

### 获取用户投递列表
```http
GET /api/v1/tracker/applications/{user_id}
```

### 更新投递状态
```http
PATCH /api/v1/applications/{application_id}/status?status={status}&notes={notes}
```

**Status 枚举:** `draft` | `applied` | `interview_invited` | `offer` | `rejected` | `withdrawn`

### 获取投递总览
```http
GET /api/v1/tracker/dashboard/{user_id}
```

**Response:**
```json
{
  "user_id": "user_001",
  "stats": {
    "total": 5,
    "draft": 1,
    "applied": 2,
    "interview_invited": 1,
    "offer": 0,
    "rejected": 1
  },
  "recent_applications": [...]
}
```

---

## 完整流程示例

```bash
# 1. 初始化 Mock 岗位
curl -X POST http://localhost:8000/api/v1/jobs/seed

# 2. 上传简历（需要真实 PDF 文件）
curl -X POST "http://localhost:8000/api/v1/resume/upload?user_id=test_user" \
  -F "file=@resume.pdf"

# 3. 计算匹配度
curl -X POST "http://localhost:8000/api/v1/jobs/match?profile_id={id}&job_id={job_id}"

# 4. 生成优化建议
curl -X POST "http://localhost:8000/api/v1/applications/optimize" \
  -H "Content-Type: application/json" \
  -d '{"resume_profile_id": "{id}", "job_id": "{job_id}"}'

# 5. 创建模拟面试
curl -X POST "http://localhost:8000/api/v1/interview/sessions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "job_id": "{job_id}"}'

# 6. 提交面试答案
curl -X POST "http://localhost:8000/api/v1/interview/sessions/{session_id}/submit" \
  -H "Content-Type: application/json" \
  -d '[{"question_index": 0, "answer": "我的回答..."}]'

# 7. 创建投递记录
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "job_id": "{job_id}", "resume_profile_id": "{id}"}'

# 8. 查看投递总览
curl http://localhost:8000/api/v1/tracker/dashboard/test_user
```
