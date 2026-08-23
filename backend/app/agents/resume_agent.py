"""
ResumeAgent — PDF 简历解析 + 用户能力画像生成
"""
import uuid
import re
from typing import Optional, List
from loguru import logger

from app.db.models import ResumeProfile
from app.db.database import get_db
from app.schemas.models import (
    ResumeProfileCreate,
    ResumeProfileResponse,
    SkillItem,
    ExperienceItem,
    EducationItem,
)


class ResumeAgent:
    """简历解析与画像生成 Agent"""

    async def parse_and_create(self, user_id, file_bytes: bytes, filename: str) -> ResumeProfileResponse:
        """上传 PDF → 解析文本 → 生成画像 → 存入 DB"""
        # 1. 解析 PDF
        parsed_text = await self._extract_text(file_bytes)
        logger.info(f"PDF 解析完成，{len(parsed_text)} 字符")

        # 2. 提取结构化信息
        extracted = await self._extract_profile(parsed_text)
        logger.info(f"提取完成: skills={len(extracted['skills'])}, exp={len(extracted['experience'])}")

        # 3. 生成能力画像摘要
        summary = await self._generate_summary(extracted)

        # 4. 存入数据库
        profile_id = str(uuid.uuid4())
        async for db in get_db():
            profile = ResumeProfile(
                id=str(uuid.uuid4()),
                user_id=int(user_id) if user_id else 1,
                original_filename=filename,
                parsed_text=parsed_text,
                skills=extracted["skills"],
                experience=extracted["experience"],
                education=extracted["education"],
                summary=summary,
                strength_analysis=extracted.get("strengths"),
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            return ResumeProfileResponse.model_validate(profile)

    async def get_profile(self, profile_id: str) -> Optional[ResumeProfileResponse]:
        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            if profile:
                return ResumeProfileResponse.model_validate(profile)
        return None

    async def _extract_text(self, file_bytes: bytes) -> str:
        """提取 PDF 文本内容（MVP 使用 pdfplumber）"""
        try:
            import pdfplumber
            from io import BytesIO
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                texts = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(texts)
        except Exception as e:
            logger.warning(f"PDF 解析失败 ({e})，使用 mock 解析")
            return self._mock_parsed_text()

    def _mock_parsed_text(self) -> str:
        return """
张小明
电话: 138-0000-0000 | 邮箱: zhangxm@example.com
教育背景: 浙江大学 · 计算机科学与技术 · 本科 · 2020-2024
实习经历:
- 阿里巴巴 · 后端开发实习生 · 2023.06-2023.09
  负责用户增长模块开发，使用 Python 和 Go 实现高并发接口
- 字节跳动 · 算法实习生 · 2023.01-2023.03
  参与推荐系统优化，A/B 测试提升点击率 5%
技能: Python, Go, Java, SQL, React, Docker, Kubernetes, Redis, MySQL
项目: 分布式任务调度系统、在线协作编辑器
        """.strip()

    async def _extract_profile(self, text: str) -> dict:
        """从文本中提取结构化信息（MVP 使用规则解析，后续可接 LLM）"""
        skills = await self._extract_skills(text)
        experience = await self._extract_experience(text)
        project_experience = await self._extract_project_experience(text)
        education = await self._extract_education(text)
        strengths = await self._analyze_strengths(skills, experience)
        return {
            "skills": [s.model_dump() for s in skills],
            "experience": [e.model_dump() for e in experience],
            "project_experience": [p.model_dump() for p in project_experience],
            "education": [e.model_dump() for e in education],
            "strengths": strengths,
        }

    async def _extract_project_experience(self, text: str) -> list:
        """提取项目经历（支持多种PDF文本格式）"""
        from app.schemas.models import ProjectExperienceItem
        projects = []

        # 先定位"项目经历"章节
        项目经历_match = re.search(r'项目经历', text)
        if not 项目经历_match:
            logger.info("[Project] 未找到'项目经历'章节")
            return []

        section_text = text[项目经历_match.start():]

        # 找到下一个章节作为边界（扩展边界关键词）
        all_sections = [
            '联系方式', '求职信息', '资格证书', '个人优势', '教育经历',
            '实习经历', '工作经历', '专业技能', '技能', '自我评价',
            '语言能力', '证书', '荣誉'
        ]
        end = len(section_text)
        for sec in all_sections:
            sec_pattern = re.compile(r'^(?:' + re.escape(sec) + r'\s*(?::|：)\s*|' + re.escape(sec) + r'\s*)', re.MULTILINE)
            next_match = sec_pattern.search(section_text)
            if next_match and next_match.start() < end:
                end = next_match.start()
        section_text = section_text[:end]
        logger.info(f"[Project] 项目章节长度: {len(section_text)} 字符")

        # 按行解析项目
        lines = section_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # 检测项目标题行：包含日期模式 (20XX.XX-20XX 或 20XX-至今)
            date_match = re.search(r'(20\d{2})[./年]\d{1,2}[-—~至](20\d{2}|至今)', line)
            if date_match and not line.startswith(('1.', '2.', '3.', '4.', '5.')):
                # 这是一个项目标题行
                project_name = ''
                role = ''

                # 尝试解析：项目名 角色 时间
                # 移除行尾的日期部分
                date_part = date_match.group(0)
                before_date = line[:date_match.start()].strip()

                # 分割项目名和角色
                parts = before_date.split()
                if parts:
                    project_name = parts[0]
                    # 角色可能是后面的部分
                    if len(parts) > 1:
                        role = ' '.join(parts[1:])

                # 收集描述行（缩进或以数字开头的行）
                description_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    # 遇到空行则跳过（可能只是格式问题）
                    if not next_line:
                        j += 1
                        continue
                    # 遇到新的项目标题行则停止（检查是否包含日期模式）
                    if re.search(r'(20\d{2})[./年]\d{1,2}[-—~至](20\d{2}|至今)', next_line):
                        break
                    # 遇到章节标题则停止
                    if re.match(r'^(联系方式|求职信息|资格证书|个人优势|教育经历|实习经历|工作经历|专业技能|技能|自我评价|语言能力|证书|荣誉)\s*[:：]?\s*$', next_line):
                        break
                    # 收集描述行
                    if next_line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                        description_lines.append(next_line)
                    elif re.match(r'^[·•\-]', next_line):
                        description_lines.append(next_line)
                    elif re.match(r'^[一二三四五六七八九十]+[.、)]', next_line):
                        description_lines.append(next_line)
                    else:
                        # 连续的描述文本（非标题行）
                        description_lines.append(next_line)
                    j += 1

                # 过滤无效项目名
                if project_name and len(project_name) >= 2 and project_name not in ('项目经历', '-'):
                    description = ' '.join(description_lines)[:500] if description_lines else ''
                    projects.append(ProjectExperienceItem(
                        project_name=project_name,
                        date=date_part,
                        role=role,
                        description=description,
                    ))
                    logger.info(f"[Project] 提取项目: {project_name}, 角色: {role}, 描述长度: {len(description)}")

                i = j
                continue

            i += 1

        logger.info(f"[Project] 共提取到 {len(projects)} 个项目经历")
        return projects[:5]

    async def _extract_skills(self, text: str) -> List[SkillItem]:
        """规则提取技能关键词"""
        skill_keywords = [
            "python", "go", "golang", "java", "javascript", "typescript",
            "react", "vue", "angular", "sql", "mysql", "postgresql", "redis",
            "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
            "machine learning", "deep learning", "nlp", "cv",
            "git", "linux", "nginx", "celery", "django", "flask", "fastapi",
            "spring", "node.js", "express", "mongodb", "elasticsearch",
        ]
        text_lower = text.lower()
        found = [kw for kw in skill_keywords if kw in text_lower]
        return [SkillItem(name=kw.capitalize(), level="intermediate") for kw in found[:15]]

    async def _extract_experience(self, text: str) -> List[ExperienceItem]:
        """规则提取实习/工作经历，严格过滤非工作经历"""
        experiences = []
        # 先定位"实习经历"章节
        实习经历_match = re.search(r'实习经历', text)
        if not 实习经历_match:
            return []
        section_text = text[实习经历_match.start():]
        # 找到下一个章节作为边界
        项目经历_match = re.search(r'项目经历', section_text)
        if 项目经历_match:
            section_text = section_text[:项目经历_match.start()]

        # 匹配格式：公司名 · 岗位名 · 时间
        # 使用更精确的模式，避免匹配到 "-" 前缀和章节标题
        pattern = r"(?:^|\n)\s*[·\-—]\s*(.+?)\s*[·]\s*([^\n·]+?)\s*[·]\s*([\d\.]+)\s*[-—]\s*([\d\.]+)?\s*\n(.+?)(?=\n[^\s]|\Z)"
        matches = re.findall(pattern, section_text, re.DOTALL)
        for m in matches:
            company = m[0].strip()
            position = m[1].strip()
            # 过滤无效公司名（如 "-"、"项目经历"等）
            if not company or company in ("-", "项目经历", "实习经历") or len(company) < 2:
                continue
            # 过滤无效岗位名
            if not position or position in ("-", "项目经历", "实习经历"):
                continue
            experiences.append(ExperienceItem(
                company=company,
                position=position,
                start_date=m[2].strip(),
                end_date=m[3].strip() if m[3] else None,
                description=m[4].strip()[:200],
            ))
        return experiences[:5]

    async def _extract_education(self, text: str) -> List[EducationItem]:
        """规则提取教育背景（支持多种PDF文本格式）"""
        educations = []

        # ── 方法1：原有单行 · 分隔格式 ──────────────────────────────
        edu_pattern = r"(?:^|\n)\s*([^\n·]+?)\s*[·]\s*([^\n·]+?)\s*[·]\s*([^\n·]+?)\s*[·]\s*([\d\.]+)\s*[-—]\s*([\d\.]+)"
        matches = re.findall(edu_pattern, text)
        for m in matches:
            school = m[0].strip()
            school = re.sub(r'^(教育背景|教育经历)\s*[:：]\s*', '', school)
            educations.append(EducationItem(
                school=school,
                degree=m[1].strip(),
                major=m[2].strip(),
                start_year=int(m[3].split(".")[0]) if m[3] else None,
                end_year=int(m[4].split(".")[0]) if m[4] else None,
            ))

        # ── 方法2：换行分隔格式 ─────────────────────────────────────
        # 检测教育背景区块，逐行解析
        edu_keywords = r'(?:教育背景|教育经历|学历|大学|学院)'
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 检测教育标题行
            if re.search(edu_keywords, line, re.IGNORECASE):
                # 尝试从同一行或后续行提取信息
                block_lines = [line]
                j = i + 1
                # 收集后续相关行（直到遇到下一个大标题）
                while j < len(lines) and j < i + 6:
                    next_line = lines[j].strip()
                    if next_line and not re.search(r'(?:工作经历|实习经历|项目经历|技能|联系方式|个人优势)', next_line):
                        block_lines.append(next_line)
                    j += 1

                # 尝试从块中提取教育信息
                block_text = ' '.join(block_lines)
                # 提取学校名（常见模式：XX大学、XX学院）
                school_match = re.search(r'([一-龥]+(?:大学|学院|系|校))', block_text)
                school = school_match.group(1) if school_match else None

                # 提取学历
                degree_match = re.search(r'(?:本科|硕士|博士|大专|专科)', block_text)
                degree = degree_match.group(0) if degree_match else '未知'

                # 提取专业
                major_match = re.search(r'(?:专业[：:]?\s*|([一-龥]+(?:计算机|软件|电子|机械|经济|管理|文学|理学|工学|医学|法学)))', block_text)
                major = major_match.group(1) if major_match else ''

                # 提取年份
                year_matches = re.findall(r'(20\d{2})\s*[-—~到至]\s*(20\d{2}|至今)', block_text)
                start_year = int(year_matches[0][0]) if year_matches else None
                end_year = int(year_matches[0][1].replace('至今', '2026')) if year_matches and year_matches[0][1] != '至今' else None

                if school:
                    educations.append(EducationItem(
                        school=school,
                        degree=degree,
                        major=major,
                        start_year=start_year,
                        end_year=end_year,
                    ))
                i = j
                continue
            i += 1

        # ── 方法3：全局扫描学校名称模式 ──────────────────────────────
        if not educations:
            school_pattern = r'([一-龥]{2,}(?:大学|学院|系|校))'
            school_matches = re.findall(school_pattern, text)
            for school in school_matches[:3]:
                # 查找该学校附近的学历和专业信息
                school_idx = text.find(school)
                context = text[max(0, school_idx-100):min(len(text), school_idx+200)]

                degree_match = re.search(r'(本科|硕士|博士|大专)', context)
                degree = degree_match.group(1) if degree_match else '未知'

                major_match = re.search(r'(计算机|软件|电子|机械|经济|管理|文学|理学|工学|医学|法学|金融|会计|外语|法律|教育)', context)
                major = major_match.group(1) if major_match else ''

                year_matches = re.findall(r'(20\d{2})\s*[-—~到至]\s*(20\d{2}|至今)', context)
                start_year = int(year_matches[0][0]) if year_matches else None
                end_year = int(year_matches[0][1].replace('至今', '2026')) if year_matches and year_matches[0][1] != '至今' else None

                educations.append(EducationItem(
                    school=school,
                    degree=degree,
                    major=major,
                    start_year=start_year,
                    end_year=end_year,
                ))

        # 去重（基于学校名）
        seen_schools = set()
        unique_educations = []
        for edu in educations:
            if edu.school and edu.school not in seen_schools:
                seen_schools.add(edu.school)
                unique_educations.append(edu)

        logger.info(f"[Education] 提取到 {len(unique_educations)} 条教育背景: {[e.school for e in unique_educations]}")
        return unique_educations[:3]

    async def _analyze_strengths(self, skills: List[dict], experience: List[dict]) -> dict:
        """生成能力优势分析"""
        strengths = []
        if len(skills) >= 5:
            strengths.append({"type": "technical", "desc": f"技术栈丰富，掌握 {len(skills)} 项技能", "score": 80})
        if len(experience) >= 2:
            strengths.append({"type": "experience", "desc": f"实习经历充实，共 {len(experience)} 段", "score": 75})
        if any("算法" in (e.get("position", "") if isinstance(e, dict) else e.position) for e in experience):
            strengths.append({"type": "algorithm", "desc": "有算法相关实习经验", "score": 85})
        return strengths if strengths else [{"type": "general", "desc": "待补充更多技能信息", "score": 50}]

    async def _generate_summary(self, extracted: dict) -> str:
        """生成用户能力画像摘要：不含时间信息，综合教育+经历+项目+技能+优势"""
        skills = extracted.get("skills", [])
        exps = extracted.get("experience", [])
        projects = extracted.get("project_experience", [])
        edus = extracted.get("education", [])

        parts = []

        # 教育背景（不含年份）
        if edus:
            edu_parts = []
            for edu in edus:
                school = edu.get("school", "") if isinstance(edu, dict) else getattr(edu, "school", "")
                degree = edu.get("degree", "") if isinstance(edu, dict) else getattr(edu, "degree", "")
                major = edu.get("major", "") if isinstance(edu, dict) else getattr(edu, "major", "")
                edu_info = school
                if degree:
                    edu_info += f"·{degree}"
                if major:
                    edu_info += f"·{major}"
                edu_parts.append(edu_info)
            parts.append(f"毕业于{'、'.join(edu_parts)}。")
        else:
            parts.append("教育背景待补充。")

        # 实习经历
        if exps:
            exp_count = len(exps)
            companies = [e.get("company", "") if isinstance(e, dict) else getattr(e, "company", "") for e in exps]
            company_str = "、".join(companies[:3]) or "多家企业"
            parts.append(f"拥有{exp_count}段实习经历，曾在{company_str}积累实践经验。")
        else:
            parts.append("实习经历待补充。")

        # 项目经历
        if projects:
            pe_count = len(projects)
            pe_names = [p.get("project_name", "") if isinstance(p, dict) else getattr(p, "project_name", "") for p in projects]
            name_str = "、".join(pe_names[:2])
            parts.append(f"主导{pe_count}个项目，包括{name_str}。")
        else:
            parts.append("项目经历待补充。")

        # 核心技能
        if skills:
            skill_names = [s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "") for s in skills[:6]]
            skill_str = "、".join(skill_names)
            parts.append(f"掌握{skill_str}等核心技能。")
        else:
            parts.append("专业技能待补充。")

        return "".join(parts)
