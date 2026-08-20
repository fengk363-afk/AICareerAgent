# AI Career Agent - 测试计划

## 测试环境

```bash
# 启动 PostgreSQL
docker run --name postgres-career \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=aicareragent \
  -p 5432:5432 \
  -d postgres:16

# 等待数据库就绪
sleep 5
```

## 后端测试

### 1. Health Check
```bash
curl http://localhost:8000/health
```
预期: `{"status":"ok","service":"AI Career Agent","version":"0.1.0"}`

### 2. 初始化 Mock 岗位
```bash
curl -X POST http://localhost:8000/api/v1/jobs/seed
```
预期: 返回 5 条岗位数据

### 3. 获取岗位列表
```bash
curl http://localhost:8000/api/v1/jobs/
```
预期: 返回岗位数组

### 4. 简历上传（需要 PDF 文件）
```bash
# 使用测试 PDF
curl -X POST "http://localhost:8000/api/v1/resume/upload?user_id=test_user" \
  -F "file=@test_files/sample_resume.pdf"
```
预期: 返回解析后的 ResumeProfile

### 5. 匹配度计算
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/match?profile_id={profile_id}&job_id={job_id}"
```
预期: 返回 MatchScoreResponse

### 6. 简历优化
```bash
curl -X POST http://localhost:8000/api/v1/applications/optimize \
  -H "Content-Type: application/json" \
  -d '{"resume_profile_id":"{profile_id}","job_id":"{job_id}"}'
```
预期: 返回优化建议

### 7. 创建模拟面试
```bash
curl -X POST http://localhost:8000/api/v1/interview/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","job_id":"{job_id}"}'
```
预期: 返回 InterviewSession（含问题列表）

### 8. 提交面试答案
```bash
curl -X POST http://localhost:8000/api/v1/interview/sessions/{session_id}/submit \
  -H "Content-Type: application/json" \
  -d '[{"question_index":0,"answer":"我在阿里巴巴实习期间负责..."},{"question_index":1,"answer":"缓存穿透是指..."}]'
```
预期: 返回带反馈的 InterviewSession

### 9. 创建投递记录
```bash
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","job_id":"{job_id}","resume_profile_id":"{profile_id}"}'
```
预期: 返回 ApplicationResponse

### 10. 投递总览
```bash
curl http://localhost:8000/api/v1/tracker/dashboard/test_user
```
预期: 返回统计数据和投递列表

## 端到端流程测试

```bash
#!/bin/bash
# test_e2e.sh
set -e

BASE="http://localhost:8000/api/v1"

echo "=== 1. 初始化 Mock 数据 ==="
JOBS=$(curl -s -X POST "$BASE/jobs/seed")
echo "岗位数: $(echo $JOBS | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')"

echo ""
echo "=== 2. 上传简历 ==="
PROFILE=$(curl -s -X POST "$BASE/resume/upload?user_id=test_user" \
  -F "file=@test_files/sample_resume.pdf")
PROFILE_ID=$(echo $PROFILE | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "Profile ID: $PROFILE_ID"

echo ""
echo "=== 3. 计算匹配度 ==="
FIRST_JOB_ID=$(echo $JOBS | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')
MATCH=$(curl -s -X POST "$BASE/jobs/match?profile_id=$PROFILE_ID&job_id=$FIRST_JOB_ID")
echo "匹配度: $(echo $MATCH | python3 -c 'import sys,json;print(json.load(sys.stdin)["overall_score"])')"

echo ""
echo "=== 4. 简历优化 ==="
OPT=$(curl -s -X POST "$BASE/applications/optimize" \
  -H "Content-Type: application/json" \
  -d "{\"resume_profile_id\":\"$PROFILE_ID\",\"job_id\":\"$FIRST_JOB_ID\"}")
echo "优化分数: $(echo $OPT | python3 -c 'import sys,json;print(json.load(sys.stdin)["improvement_score"])')"

echo ""
echo "=== 5. 模拟面试 ==="
INTERVIEW=$(curl -s -X POST "$BASE/interview/sessions" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test_user\",\"job_id\":\"$FIRST_JOB_ID\"}")
SESSION_ID=$(echo $INTERVIEW | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
QUESTION_COUNT=$(echo $INTERVIEW | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["questions"]))')
echo "面试会话: $SESSION_ID, 问题数: $QUESTION_COUNT"

echo ""
echo "=== 6. 提交面试答案 ==="
ANSWERS='[{"question_index":0,"answer":"我在阿里巴巴实习期间负责后端开发，使用Python和Go构建了高并发服务"},{"question_index":1,"answer":"缓存穿透是指查询不存在的数据，解决方案包括缓存空值和使用布隆过滤器"}]'
FEEDBACK=$(curl -s -X POST "$BASE/interview/sessions/$SESSION_ID/submit" \
  -H "Content-Type: application/json" \
  -d "$ANSWERS")
OVERALL=$(echo $FEEDBACK | python3 -c 'import sys,json;print(json.load(sys.stdin)["overall_score"])')
echo "面试总分: $OVERALL"

echo ""
echo "=== 7. 创建投递记录 ==="
APP=$(curl -s -X POST "$BASE/applications/" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test_user\",\"job_id\":\"$FIRST_JOB_ID\",\"resume_profile_id\":\"$PROFILE_ID\"}")
APP_ID=$(echo $APP | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "投递 ID: $APP_ID"

echo ""
echo "=== 8. 查看投递总览 ==="
DASHBOARD=$(curl -s "$BASE/tracker/dashboard/test_user")
echo "总投递: $(echo $DASHBOARD | python3 -c 'import sys,json;print(json.load(sys.stdin)["stats"]["total"])')"
echo "已投递: $(echo $DASHBOARD | python3 -c 'import sys,json;print(json.load(sys.stdin)["stats"]["applied"])')"

echo ""
echo "✅ 端到端测试完成！"
```

## 前端测试

```bash
# 启动前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

测试流程:
1. 首页上传 PDF → 跳转到简历画像页
2. 简历画像页查看技能/经历/教育 → 点击"查看推荐岗位"
3. 岗位列表页查看匹配度 → 点击"模拟面试"或"优化简历"
4. 面试页面回答问题 → 查看反馈
5. 投递追踪页面查看进度
