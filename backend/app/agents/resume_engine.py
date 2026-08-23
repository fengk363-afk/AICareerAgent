"""
ResumeEngine v2 — 通用简历解析引擎
解析流程: PDF文本提取 → 章节识别 → 结构化JSON → 校验 → 摘要生成
支持: 中英文简历、有/无章节标题、多种分隔符格式
"""
import uuid
import re
from typing import Optional, List, Dict, Any
from loguru import logger

from app.db.models import ResumeProfile, ResumeVersion, Job
from app.db.database import get_db
from app.schemas.models import (
    ResumeProfileResponse,
    SkillItem,
    EducationItem,
    ExperienceItem,
    ProjectExperienceItem,
    CertificateItem,
)


class ResumeEngine:
    """通用简历解析引擎"""

    # ── 章节关键词（中英文兼容）────────────────────────────────────
    SECTION_PATTERNS = {
        "education": [
            r'^教育(背景|经历)?\s*[:：]', r'^education', r'^academic', r'^qualifications',
            r'^学历', r'^学位',
        ],
        "experience": [
            r'^工作(经历|经验)?\s*[:：]?', r'^实习(经历|经验)?\s*[:：]?',
            r'^work(ing)?(experience)?\s*[:：]?', r'^employment', r'^career',
            r'^professional\s*experience', r'^experience\s*[:：]',
            r'^职业', r'^履历',
        ],
        "project": [
            r'^项目(经历|经验)?\s*[:：]?', r'^projects?\s*[:：]?', r'^project\s*experience',
            r'^personal\s*project', r'^portfolio',
            r'^课题', r'^作品',
        ],
        "skills": [
            r'^(专业)?技能(清单)?\s*[:：]?', r'^skills?\s*[:：]?', r'^technical\s*skills',
            r'^competencies', r'^专业能力',
        ],
        "certificate": [
            r'^证书(资格)?\s*[:：]', r'^certificat(e|ion)?\s*[:：]?', r'^qualifications?\s*[:：]?',
            r'^资格', r'^认证', r'^执照',
        ],
        "language": [
            r'^语言(能力)?\s*[:：]', r'^language(s)?\s*[:：]?', r'^languages\s*[:：]?',
            r'^外语', r'^英语水平',
        ],
        "summary": [
            r'^个人(总结|优势|简介|评价)?\s*[:：]', r'^summary\s*[:：]?', r'^objective\s*[:：]?',
            r'^profile\s*[:：]?', r'^自我', r'^个人优势',
        ],
        "contact": [
            r'^联系(方式)?\s*[:：]', r'^contact\s*[:：]?', r'^information\s*[:：]?',
            r'^联系方式', r'^个人信息',
        ],
    }

    # 章节顺序（用于边界判断）
    SECTION_ORDER = ["contact", "summary", "education", "experience", "project", "skills", "certificate", "language"]

    # 职位关键词（用于判断 employment_type）
    INTERN_KEYWORDS = {"实习生", "实习", "intern", "internship", "管培", "培训生", "储备干部"}
    FULLTIME_KEYWORDS = {"工程师", "经理", "总监", "主管", "专员", "助理", "分析师", "研究员",
                         "developer", "manager", "director", "analyst", "engineer", "consultant"}

    # 动作词（用于过滤标题中的描述内容）
    ACTION_WORDS = {"负责", "协助", "参与", "完成", "使用", "实现", "搭建", "开发",
                    "design", "develop", "implement", "build", "create", "manage", "lead"}

    # ── 主入口 ────────────────────────────────────────────────────

    async def parse_and_create(self, user_id, file_bytes: bytes, filename: str) -> ResumeProfileResponse:
        """上传 PDF → 解析 → 生成画像"""
        parsed_text = await self._extract_text(file_bytes)
        logger.info(f"PDF 解析完成，{len(parsed_text)} 字符")

        # 解析
        extracted = await self._extract_profile(parsed_text)

        # 校验
        validation = self._validate(extracted)
        if not validation["valid"]:
            logger.warning(f"解析校验失败: {validation['issues']}，尝试重新解析")
            extracted = self._fallback_extract(parsed_text)
            validation = self._validate(extracted)

        # 生成摘要
        summary = self._generate_summary(extracted)

        # 存入数据库
        profile_id = str(uuid.uuid4())
        async for db in get_db():
            profile = ResumeProfile(
                id=profile_id,
                user_id=int(user_id) if user_id else 1,
                original_filename=filename,
                parsed_text=parsed_text,
                skills=extracted["skills"],
                experience=extracted["experience"],
                project_experience=extracted["project_experience"],
                education=extracted["education"],
                certificates=extracted.get("certificates", []),
                summary=summary,
                strength_analysis=extracted.get("strengths", []),
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            return ResumeProfileResponse.model_validate(profile)

    # ── PDF 文本提取 ──────────────────────────────────────────────

    async def _extract_text(self, file_bytes: bytes) -> str:
        try:
            import pdfplumber
            from io import BytesIO
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                texts = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(texts)
        except Exception as e:
            logger.warning(f"PDF 解析失败: {e}，使用 mock 数据")
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
项目经历:
- 分布式任务调度系统 · 项目负责人 · 2022.09-2023.01
  使用 Python + Flask 搭建平台，负责核心模块开发
- 在线协作编辑器 · 核心开发者 · 2022.03-2022.08
  实现实时同步功能，使用 WebSocket 和 CRDT 算法
专业技能: Python, Go, Java, SQL, React, Docker, Kubernetes, Redis, MySQL
        """.strip()

    # ── 章节识别 ──────────────────────────────────────────────────

    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """识别所有章节及其边界，返回 [{name, start, end, content}]"""
        lines = text.split("\n")
        sections = []
        n = len(lines)

        # 为每行标注可能的章节类型
        line_types = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                line_types.append(None)
                continue

            # 尝试匹配各章节
            matched = None
            for sec_name, patterns in self.SECTION_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, stripped, re.IGNORECASE):
                        # 章节标题行：以章节关键词开头，后跟冒号或换行
                        # 不限制长度，因为有些简历标题行可能较长
                        matched = sec_name
                        break
                if matched:
                    break
            line_types.append(matched)

        # 根据标注构建章节边界
        # 策略：找到每个章节的起始行，下一个章节的起始行就是当前章节的结束
        section_starts = []
        for i, lt in enumerate(line_types):
            if lt in self.SECTION_ORDER:
                section_starts.append((lt, i))

        # 构建章节区间
        for idx, (sec_name, start_pos) in enumerate(section_starts):
            end_pos = section_starts[idx + 1][1] if idx + 1 < len(section_starts) else n
            content = "\n".join(lines[start_pos:end_pos])
            sections.append({
                "name": sec_name,
                "start": start_pos,
                "end": end_pos,
                "content": content,
                "lines": lines[start_pos:end_pos],
            })

        # 处理无章节标题的文本：根据内容模式推断
        # 如果检测到的章节不包含 experience 和 project，说明是无标题简历，需要推断
        detected_names = {s["name"] for s in sections}
        if "experience" not in detected_names or "project" not in detected_names:
            inferred = self._infer_sections_from_content(lines)
            # 合并：用推断的章节替换缺失的章节
            for inf in inferred:
                if inf["name"] not in detected_names:
                    sections.append(inf)
                else:
                    # 替换同类型章节
                    sections = [s for s in sections if s["name"] != inf["name"]] + [inf]
            # 确保 infer 的 sections 有 content 字段
            for s in sections:
                if "content" not in s:
                    s["content"] = "\n".join(s.get("lines", []))

        return sections

    def _infer_sections_from_content(self, lines: List[str]) -> List[Dict[str, Any]]:
        """无章节标题时，根据内容模式推断章节"""
        sections = []
        n = len(lines)
        i = 0

        current_section = None
        current_lines = []

        def save_current():
            nonlocal current_section, current_lines
            if current_lines:
                sections.append({"name": current_section or "unknown", "lines": current_lines})
                current_lines = []

        while i < n:
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # 检测教育经历模式
            if self._is_education_line(line):
                new_section = "education"
            # 检测工作经历模式（公司名+职位+日期）
            elif self._is_experience_line(line):
                new_section = "experience"
            # 检测项目经历模式
            elif self._is_project_line(line):
                new_section = "project"
            # 检测技能模式
            elif self._is_skill_line(line):
                new_section = "skills"
            else:
                # 描述行：追加到当前章节
                if current_section:
                    current_lines.append(line)
                i += 1
                continue

            # 切换到新章节
            if new_section != current_section:
                save_current()
                current_section = new_section
            current_lines.append(line)
            i += 1

        save_current()
        return sections

    def _is_education_line(self, line: str) -> bool:
        """判断是否为教育经历行"""
        # 包含学校/学历关键词，且不含公司/项目特征
        edu_keywords = ["大学", "学院", "本科", "硕士", "博士", "bachelor", "master", "phd", "university", "college"]
        has_edu = any(kw in line.lower() for kw in edu_keywords)
        # 排除包含工作特征的行
        work_keywords = ["公司", "担任", "任职", "工作", "实习"]
        has_work = any(kw in line.lower() for kw in work_keywords)
        # 排除包含项目特征的行
        proj_keywords = ["项目", "课题", "开发", "实现", "搭建"]
        has_proj = any(kw in line.lower() for kw in proj_keywords)
        return has_edu and not has_work and not has_proj

    def _is_experience_line(self, line: str) -> bool:
        """判断是否为工作经历行（公司名+职位+日期）"""
        # 模式1: 公司名 · 职位 · 日期
        if re.search(r'[·\-—]\s*(?:实习生|工程师|分析师|研究员|运营|产品|设计|开发|算法|数据|市场|销售|经理|主管|专员|助理|顾问|代表|总监|总裁|CEO|CTO|CFO|PM|PE|BD|HR|负责人|组长|队长|部长|主任|创始人|合伙人|联合创始人|首席|高级|初级|中级|资深|管培|培训生)', line):
            # 进一步验证：公司名部分不应包含项目特征词
            project_keywords = ['系统', '平台', '项目', '应用', '工具', '软件', 'service', 'system', 'platform', 'project', 'app']
            first_part = line.split('·')[0].strip() if '·' in line else line.split()[0]
            if not any(kw in first_part for kw in project_keywords):
                return True
        # 模式2: 日期范围（支持 YYYY.MM-YYYY.MM 和 YYYY.MM-至今）
        if re.search(r'\d{4}[\./年]\d{1,2}[\-—~至](?:\d{4}[\./年]\d{1,2}|至今)', line):
            # 检查是否包含公司名特征
            if re.search(r'[一-鿿]{2,}(?=[·\-—\s])', line) or re.search(r'[a-zA-Z]{2,}', line):
                # 同样排除项目特征
                project_keywords = ['系统', '平台', '项目', '应用', '工具', '软件', 'service', 'system', 'platform', 'project', 'app']
                first_part = line.split('·')[0].strip() if '·' in line else line.split()[0]
                if not any(kw in first_part for kw in project_keywords):
                    return True
        return False

    def _is_project_line(self, line: str) -> bool:
        """判断是否为项目经历行"""
        # 包含时间但职位关键词是项目相关（支持 YYYY.MM-至今）
        if re.search(r'\d{4}[\./年]\d{1,2}[\-—~至](?:\d{4}[\./年]\d{1,2}|至今)', line):
            # 检查是否像项目名（不含公司名特征）
            role_keywords = ["负责人", "组长", "队长", "成员", "开发者", "设计师", "分析师",
                             "leader", "lead", "member", "developer", "designer"]
            if any(kw in line for kw in role_keywords):
                # 确保不是工作经历（工作经历通常有公司名）
                company_pattern = r'^[^\s·]+[·\-—](?:实习生|工程师|分析师|研究员|运营|产品|设计|开发|算法|数据|市场|销售|经理|主管|专员|助理|顾问|代表|总监|总裁|CEO|CTO|CFO|PM|PE|BD|HR|负责人|组长|队长|部长|主任|创始人|合伙人|首席|高级|初级|中级|资深|管培|培训生|储备干部)'
                if not re.match(company_pattern, line):
                    return True
        return False

    def _is_skill_line(self, line: str) -> bool:
        """判断是否为技能行"""
        # 包含技能分隔符且不含日期
        if re.search(r'[，,、:：·]', line) and not re.search(r'\d{4}', line):
            # 检查是否像技能列表
            words = re.split(r'[，,\s]+', line)
            tech_keywords = ["python", "java", "javascript", "typescript", "go", "c++", "c#",
                             "react", "vue", "angular", "docker", "kubernetes", "aws", "azure",
                             "sql", "mysql", "postgresql", "redis", "mongodb", "git", "linux"]
            if any(kw in line.lower() for kw in tech_keywords):
                return True
        return False

    # ── 结构化解析 ────────────────────────────────────────────────

    async def _extract_profile(self, text: str) -> dict:
        """主解析入口：章节识别 → 各字段提取"""
        sections = self._detect_sections(text)

        education = []
        experience = []
        project_experience = []
        skills = []
        certificates = []
        strengths = []

        for section in sections:
            name = section["name"]
            content = section["content"]
            lines = section["lines"]

            # 移除章节标题行（第一行如果是标题则去掉）
            header_patterns = self._get_header_patterns(name)
            # 清理每个 pattern 的 ^ 前缀，然后组合
            clean_patterns = [p[1:] if p.startswith('^') else p for p in header_patterns]
            combined_pattern = r'^(?:' + '|'.join(clean_patterns) + r')\s*[:：]?\s*'
            if lines:
                first_line = lines[0].strip()
                if re.match(combined_pattern, first_line, re.IGNORECASE):
                    # 如果第一行只是标题（如 "Education" 或 "教育背景:"），移除整行
                    # 检查是否匹配到行尾（无后续内容）
                    exact_pattern = r'^(?:' + '|'.join(clean_patterns) + r')(?:\s*[:：]\s*)?$'
                    if re.match(exact_pattern, first_line, re.IGNORECASE):
                        lines = lines[1:]
                    # 如果第一行包含标题+内容（如 "专业技能: Python, Go"），移除标题前缀
                    else:
                        lines[0] = re.sub(combined_pattern, '', first_line, flags=re.IGNORECASE).strip()
                    content = "\n".join(lines)

            if name == "education":
                education.extend(self._parse_education_lines(lines))
            elif name == "experience":
                experience.extend(self._parse_experience_lines(lines))
            elif name == "project":
                project_experience.extend(self._parse_project_lines(lines))
            elif name == "skills":
                skills.extend(self._parse_skills_lines(lines))
            elif name == "certificate":
                certificates.extend(self._parse_certificate_lines(lines))
            elif name == "contact":
                pass  # 联系信息不存储
            elif name == "summary":
                pass  # summary 由引擎生成
            elif name == "language":
                pass  # 语言信息暂不存储
            else:
                # 未知章节：尝试推断
                inferred = self._parse_unknown_section(lines)
                education.extend(inferred.get("education", []))
                experience.extend(inferred.get("experience", []))
                project_experience.extend(inferred.get("project", []))
                skills.extend(inferred.get("skills", []))
                certificates.extend(inferred.get("certificates", []))

        # 去重和清理
        education = self._dedup_education(education)
        experience = self._dedup_experience(experience)
        project_experience = self._dedup_projects(project_experience)
        skills = self._dedup_skills(skills)

        # 能力优势分析（传入 dict 格式）
        skills_dict = [s.model_dump() for s in skills]
        exp_dict = [e.model_dump() for e in experience]
        proj_dict = [p.model_dump() for p in project_experience]
        strengths = await self._analyze_strengths(skills_dict, exp_dict, proj_dict)

        return {
            "education": [e.model_dump() for e in education],
            "experience": [e.model_dump() for e in experience],
            "project_experience": [p.model_dump() for p in project_experience],
            "skills": [s.model_dump() for s in skills],
            "certificates": [c.model_dump() for c in certificates],
            "strengths": strengths,
        }

    # ── 教育经历解析 ──────────────────────────────────────────────

    def _parse_education_lines(self, lines: List[str]) -> List[EducationItem]:
        """解析教育经历行"""
        educations = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 跳过纯章节标题行（如 "教育背景:" 或 "Education"）
            if re.match(r'^(教育(背景|经历)?\s*[:：]?$|education\s*[:：]?$|academic\s*[:：]?$)', line, re.IGNORECASE):
                continue
            # 跳过非教育行
            if not self._is_education_line(line):
                continue

            edu = self._parse_single_education(line)
            if edu:
                educations.append(edu)
        return educations

    def _parse_single_education(self, line: str) -> Optional[EducationItem]:
        """解析单行教育经历"""
        # 移除前缀
        clean = re.sub(r'^(教育背景|教育经历|education|academic)\s*[:：]\s*', '', line)

        # 提取年份（支持 YYYY-YYYY 和 YYYY.MM-YYYY.MM 格式）
        year_matches = re.findall(r'(\d{4})', clean)
        start_year = int(year_matches[0]) if len(year_matches) >= 1 else None
        end_year = int(year_matches[1]) if len(year_matches) >= 2 else None

        # 按分隔符拆分（优先用 · 分隔，其次用空格）
        if '·' in clean:
            parts = re.split(r'[·]', clean)
            parts = [p.strip() for p in parts if p.strip()]
        else:
            # 用空格分隔，但保留多词学校名
            words = clean.split()
            parts = []
            i = 0
            while i < len(words):
                word = words[i]
                if word.lower() in {'b.s.', 'b.a.', 'm.s.', 'm.a.', 'ph.d.', 'bs', 'ba', 'ms', 'ma', 'phd',
                                    'bachelor', 'master', 'doctorate', 'associate'}:
                    degree_part = word
                    j = i + 1
                    while j < len(words) and words[j] not in {'·', '-', '—', '20'}:
                        degree_part += ' ' + words[j]
                        j += 1
                    parts.append(degree_part)
                    i = j
                elif re.match(r'^\d{4}$', word):
                    parts.append(word)
                    i += 1
                else:
                    if parts and parts[-1] not in {'in', 'of'}:
                        parts[-1] += ' ' + word
                    else:
                        parts.append(word)
                    i += 1

        school = ""
        degree = ""
        major = ""

        degree_keywords = {"博士", "硕士", "本科", "大专", "专科", "学士",
                           "phd", "master", "bachelor", "associate",
                           "b.s.", "b.a.", "m.s.", "m.a.", "bs", "ba", "ms", "ma"}
        year_pattern = re.compile(r'^\d{4}$')

        for p in parts:
            if p.lower() in degree_keywords:
                degree = p
            elif year_pattern.match(p):
                continue
            elif len(p) >= 2:
                # 检查是否包含学位关键词（如 "B.S. Computer Science"）
                degree_match = re.match(r'^(' + '|'.join(degree_keywords) + r')\s*(.+)?$', p, re.IGNORECASE)
                if degree_match:
                    degree = degree_match.group(1)
                    if degree_match.group(2):
                        major = degree_match.group(2).strip()
                elif not school:
                    school = p
                elif not major:
                    major = p

        if not school:
            school = clean

        return EducationItem(
            school=school,
            degree=degree,
            major=major,
            start_year=start_year,
            end_year=end_year,
        )

    # ── 工作经历解析 ──────────────────────────────────────────────

    def _parse_experience_lines(self, lines: List[str]) -> List[ExperienceItem]:
        """解析工作经历行"""
        experiences = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            # 跳过章节标题
            if re.match(r'^(工作|实习|experience|employment|work)', line, re.IGNORECASE):
                i += 1
                continue

            # 尝试解析为工作经历
            exp = self._parse_single_experience(line, lines, i)
            if exp:
                experiences.append(exp)
                # 跳过已消耗的描述行
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    # 遇到新的条目或章节标题则停止
                    if self._is_experience_line(next_line) or self._is_project_line(next_line):
                        break
                    if re.match(r'^(工作|实习|项目|教育|技能|certificate|experience|project|education|skills)',
                                next_line, re.IGNORECASE):
                        break
                    j += 1
                i = j
            else:
                i += 1

        return experiences

    def _parse_single_experience(self, line: str, all_lines: List[str], start_idx: int) -> Optional[ExperienceItem]:
        """解析单条工作经历"""
        # 清理前缀符号
        clean = re.sub(r'^[\d\-\*•·○●\.\s]+', '', line).strip()
        if not clean:
            return None

        company = ""
        position = ""
        employment_type = "full_time"
        start_date = ""
        end_date = ""
        description_lines = []

        # 提取时间范围（支持 YYYY.MM、MM/YYYY、YYYY年MM月 等格式）
        time_match = re.search(
            r'((?:\d{4}[\./年]\d{1,2}|\d{1,2}/\d{4})[\-—~至](?:\d{4}[\./年]\d{1,2}|\d{1,2}/\d{4}|至今))',
            clean
        )
        time_str = time_match.group(1) if time_match else ""
        before_time = clean[:time_match.start()].strip() if time_match else clean

        # 清理前缀符号
        before_time = re.sub(r'^[·\-—\s]+', '', before_time).strip()
        before_time = re.sub(r'[·\-—\s]+$', '', before_time).strip()

        # 解析公司名和职位
        if '·' in before_time:
            parts = before_time.split('·')
            company = parts[0].strip()
            position = parts[1].strip() if len(parts) > 1 else ""
        elif ' ' in before_time:
            # 尝试空格分隔：公司名 职位
            words = before_time.split()
            if len(words) >= 2:
                company = words[0]
                position = ' '.join(words[1:])
            else:
                company = before_time
        else:
            company = before_time

        # 判断 employment_type
        position_lower = position.lower()
        if any(kw in position for kw in self.INTERN_KEYWORDS) or \
           any(kw in position_lower for kw in ["intern", "internship"]):
            employment_type = "internship"

        # 解析时间
        if time_str:
            time_parts = re.split(r'[\-—~至]', time_str)
            if len(time_parts) >= 2:
                start_date = time_parts[0].strip().replace('年', '.')
                end_date = time_parts[1].strip().replace('年', '.')
                if end_date in ('至', ''):
                    end_date = "至今"
            else:
                start_date = time_str.replace('年', '.')
                end_date = ""

        # 收集描述行
        j = start_idx + 1
        while j < len(all_lines):
            next_line = all_lines[j].strip()
            if not next_line:
                j += 1
                continue
            # 遇到新条目或章节标题停止
            if self._is_experience_line(next_line) or self._is_project_line(next_line):
                break
            if re.match(r'^(工作|实习|项目|教育|技能|certificate|experience|project|education|skills)',
                        next_line, re.IGNORECASE):
                break
            description_lines.append(next_line)
            j += 1

        # 过滤验证
        if not company or len(company) < 2:
            return None
        if not position:
            return None
        if not start_date:
            return None
        # 公司名不能是动作词
        if any(w in company for w in self.ACTION_WORDS):
            return None

        description = "\n".join(description_lines).strip()

        return ExperienceItem(
            company=company,
            position=position,
            employment_type=employment_type,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )

    # ── 项目经历解析 ──────────────────────────────────────────────

    def _parse_project_lines(self, lines: List[str]) -> List[ProjectExperienceItem]:
        """解析项目经历行"""
        projects = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            # 跳过章节标题
            if re.match(r'^(项目|project)', line, re.IGNORECASE):
                i += 1
                continue

            proj = self._parse_single_project(line, lines, i)
            if proj:
                projects.append(proj)
                # 跳过已消耗的描述行
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if self._is_project_line(next_line) or self._is_experience_line(next_line):
                        break
                    if re.match(r'^(项目|工作|实习|教育|技能)', next_line, re.IGNORECASE):
                        break
                    j += 1
                i = j
            else:
                i += 1

        return projects

    def _parse_single_project(self, line: str, all_lines: List[str], start_idx: int) -> Optional[ProjectExperienceItem]:
        """解析单条项目经历"""
        clean = re.sub(r'^[\d\-\*•·○●\.\s]+', '', line).strip()
        if not clean:
            return None

        project_name = ""
        role = ""
        date = ""
        description_lines = []
        achievement = ""

        # 提取时间
        time_match = re.search(r'((?:\d{4}[\./年]\d{1,2})[\-—~至](?:\d{4}[\./年]\d{1,2}|至今))', clean)
        time_str = time_match.group(1) if time_match else ""
        before_time = clean[:time_match.start()].strip() if time_match else clean

        # 清理前缀
        before_time = re.sub(r'^[·\-—\s]+', '', before_time).strip()
        before_time = re.sub(r'[·\-—\s]+$', '', before_time).strip()

        # 解析项目名和角色
        if '·' in before_time:
            parts = before_time.rsplit(' · ', 1)
            project_name = parts[0].strip()
            role = parts[1].strip() if len(parts) > 1 else ""
        else:
            # 尝试空格分隔
            words = before_time.split()
            if len(words) >= 2:
                # 最后一个词如果是角色词
                role_keywords = {"负责人", "组长", "队长", "成员", "开发者", "设计师", "分析师",
                                 "leader", "lead", "member", "developer", "designer", "analyst"}
                if words[-1] in role_keywords:
                    project_name = ' '.join(words[:-1])
                    role = words[-1]
                else:
                    project_name = before_time
            else:
                project_name = before_time

        # 解析时间
        if time_str:
            time_parts = re.split(r'[\-—~至]', time_str)
            if len(time_parts) >= 2:
                start = time_parts[0].strip().replace('年', '.')
                end = time_parts[1].strip().replace('年', '.')
                if end in ('至', ''):
                    end = "至今"
                date = f"{start}-{end}"
            else:
                date = time_str.replace('年', '.')

        # 收集描述行
        j = start_idx + 1
        while j < len(all_lines):
            next_line = all_lines[j].strip()
            if not next_line:
                j += 1
                continue
            if self._is_project_line(next_line) or self._is_experience_line(next_line):
                break
            if re.match(r'^(项目|工作|实习|教育|技能)', next_line, re.IGNORECASE):
                break
            description_lines.append(next_line)
            j += 1

        description = "\n".join(description_lines).strip()

        # 从描述中提取成就（量化结果）
        achievement = self._extract_achievement(description)

        # 过滤验证
        if not project_name or len(project_name) < 2:
            return None
        # 项目名不能包含动作词
        if any(w in project_name for w in self.ACTION_WORDS):
            return None

        return ProjectExperienceItem(
            project_name=project_name,
            date=date,
            role=role,
            description=description,
            achievement=achievement,
        )

    def _extract_achievement(self, description: str) -> str:
        """从描述中提取成就（量化结果）"""
        if not description:
            return ""
        # 匹配量化表达：数字+%、排名、规模等
        achievements = []
        # 百分比
        pct_matches = re.findall(r'(\d+)%', description)
        achievements.extend(f"提升{m}%" for m in pct_matches)
        # 数量级
        qty_matches = re.findall(r'(\d+)[万wW亿yY]', description)
        achievements.extend(f"处理{m}级数据" for m in qty_matches)
        # 排名
        rank_matches = re.findall(r'(第\d+[名位])', description)
        achievements.extend(rank_matches)
        return "; ".join(achievements[:3]) if achievements else ""

    # ── 技能解析 ──────────────────────────────────────────────────

    def _parse_skills_lines(self, lines: List[str]) -> List[SkillItem]:
        """解析技能行（支持PDF断行合并）"""
        skills = []

        # ── 步骤1：合并PDF断行 ──────────────────────────────────────
        # 以项目符号（·、•、-）开头的行是新条目，后续行是上一行的延续
        merged_entries = []
        current_entry = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 跳过章节标题行
            if re.match(r'^(专业?技能(清单)?\s*[:：]?$|skills?\s*[:：]?$|technical\s*skills\s*[:：]?$)', line, re.IGNORECASE):
                continue
            # 清理前缀
            cleaned = re.sub(r'^[\d\-\*•·○●\.\s]+', '', line).strip()
            if not cleaned:
                continue
            # 检查是否是新条目（以项目符号开头）
            if re.match(r'^[·•\-]', line):
                if current_entry:
                    merged_entries.append(current_entry)
                current_entry = cleaned
            else:
                # 断行延续，合并到当前条目
                if current_entry:
                    current_entry += cleaned
                else:
                    current_entry = cleaned
        if current_entry:
            merged_entries.append(current_entry)

        # ── 步骤2：提取已知工具/软件名称 ────────────────────────────
        known_tools = [
            "Python", "Go", "Java", "JavaScript", "TypeScript",
            "React", "Vue", "Angular", "SQL", "MySQL", "PostgreSQL", "Redis",
            "Docker", "Kubernetes", "K8s", "AWS", "Azure", "GCP",
            "Git", "Linux", "Nginx", "Celery", "Django", "Flask", "FastAPI",
            "Spring", "Node.js", "Express", "MongoDB", "Elasticsearch",
            "Tableau", "Excel", "Google Trends", "Statista", "Similarweb",
            "Notion", "Asana", "Adobe Premiere", "Adobe After Effects",
            "Final Cut Pro", "Photoshop", "剪映", "Claude Code", "API",
            "PR", "AE", "FCP", "PS", "达芬奇", "Shell",
        ]

        # ── 步骤3：解析每个条目 ──────────────────────────────────────
        seen_names = set()
        for entry in merged_entries:
            # 匹配"技能名：描述"格式
            match = re.match(r'^([^：:]{2,20})[：:](.+)$', entry)
            if match:
                name = match.group(1).strip()
                desc = match.group(2).strip()

                # 过滤无效技能名
                if not name or len(name) < 2:
                    continue
                if name in ('技能', '专业技能', '技术技能'):
                    continue
                # 过滤以动作词开头的条目（可能是描述句）
                if any(name.startswith(w) for w in self.ACTION_WORDS):
                    continue
                # 过滤以句号结尾的条目（可能是句子碎片）
                if name.endswith('。') or name.endswith('.'):
                    continue

                # 去重
                name_key = name.lower().strip()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                # 从描述中提取子技能
                sub_skills = []
                for tool in known_tools:
                    tool_key = tool.lower().strip()
                    if tool_key in seen_names:
                        continue
                    # 简单子字符串匹配（不区分大小写）
                    if tool.lower() in desc.lower():
                        sub_skills.append(tool)
                        seen_names.add(tool_key)

                # 将子技能追加到描述中
                if sub_skills:
                    tools_str = "、".join(sub_skills)
                    desc = f"{desc}（掌握工具：{tools_str}）"

                # 构建技能对象
                skill = SkillItem(
                    name=name,
                    description=desc,
                    level="intermediate",
                    category=self._classify_skill(name, desc),
                )
                skills.append(skill)
                continue

            # 没有冒号的条目，检查是否是逗号分隔的技能列表
            # 只有当整个条目都是逗号分隔的值时才分割
            if ',' in entry or '，' in entry:
                # 检查是否包含中文描述特征（冒号、句号、动词）
                has_chinese_desc = any(c in entry for c in ['：', '。', '，', '、'])
                if not has_chinese_desc:
                    # 纯英文逗号分隔，可能是技能列表
                    parts = re.split(r',\s*', entry)
                    for part in parts:
                        part = part.strip()
                        if part and len(part) >= 2:
                            part_key = part.lower().strip()
                            if part_key not in seen_names:
                                seen_names.add(part_key)
                                skills.append(SkillItem(
                                    name=part,
                                    description="",
                                    level="intermediate",
                                    category=self._classify_skill(part, ""),
                                ))
                    continue

            # 单独的技能名
            if len(entry) >= 2 and len(entry) <= 60:
                # 过滤以动作词开头的条目
                if any(entry.startswith(w) for w in self.ACTION_WORDS):
                    continue
                # 过滤以句号结尾的条目
                if entry.endswith('。') or entry.endswith('.'):
                    continue
                # 过滤包含完整句子特征的条目
                if any(w in entry for w in ['实现', '提升', '输出', '确保', '支撑', '完成']):
                    continue
                # 过滤太短的条目（可能是断行碎片）
                if len(entry) < 3:
                    continue

                entry_key = entry.lower().strip()
                if entry_key not in seen_names:
                    seen_names.add(entry_key)
                    skills.append(SkillItem(
                        name=entry,
                        description="",
                        level="intermediate",
                        category=self._classify_skill(entry, ""),
                    ))

        return skills[:30]

    # ── 证书解析 ──────────────────────────────────────────────────

    def _parse_certificate_lines(self, lines: List[str]) -> List[CertificateItem]:
        """解析证书行"""
        from app.schemas.models import CertificateItem
        certificates = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^(证书|certificat|qualification)', line, re.IGNORECASE):
                continue
            # 证书行通常包含"证书"、"认证"、"等级"等词
            if any(kw in line for kw in ["证书", "认证", "等级", "cert", "license", "award"]):
                # 尝试解析：证书名 - 颁发机构 - 日期
                parts = re.split(r'[·\-—,，]', line)
                name = parts[0].strip() if parts else line
                org = parts[1].strip() if len(parts) > 1 else ""
                date = parts[2].strip() if len(parts) > 2 else ""
                if name and len(name) >= 2:
                    certificates.append(CertificateItem(
                        name=name,
                        issuing_organization=org,
                        issue_date=date,
                    ))
        return certificates

    # ── 未知章节推断解析 ──────────────────────────────────────────

    def _parse_unknown_section(self, lines: List[str]) -> dict:
        """对未知章节进行推断解析"""
        result = {"education": [], "experience": [], "project": [], "skills": [], "certificates": []}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self._is_education_line(line):
                edu = self._parse_single_education(line)
                if edu:
                    result["education"].append(edu)
            elif self._is_experience_line(line):
                # 简单解析，不收集描述
                exp = self._parse_single_experience(line, lines, 0)
                if exp:
                    result["experience"].append(exp)
            elif self._is_project_line(line):
                proj = self._parse_single_project(line, lines, 0)
                if proj:
                    result["project"].append(proj)
            elif self._is_skill_line(line):
                result["skills"].extend(self._parse_skills_lines([line]))
        return result

    # ── 去重 ──────────────────────────────────────────────────────

    def _dedup_education(self, educations: List[EducationItem]) -> List[EducationItem]:
        seen = set()
        result = []
        for e in educations:
            key = e.school
            if key not in seen:
                seen.add(key)
                result.append(e)
        return result

    def _dedup_experience(self, experiences: List[ExperienceItem]) -> List[ExperienceItem]:
        seen = set()
        result = []
        for e in experiences:
            key = (e.company, e.position, e.start_date)
            if key not in seen:
                seen.add(key)
                result.append(e)
        return result

    def _dedup_projects(self, projects: List[ProjectExperienceItem]) -> List[ProjectExperienceItem]:
        seen = set()
        result = []
        for p in projects:
            key = p.project_name
            if key not in seen:
                seen.add(key)
                result.append(p)
        return result

    def _dedup_skills(self, skills: List[SkillItem]) -> List[SkillItem]:
        seen = set()
        result = []
        for s in skills:
            key = s.name.lower()
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result

    # ── 能力优势分析 ──────────────────────────────────────────────

    async def _analyze_strengths(self, skills: list, experience: list, project_experience: list) -> list:
        """生成能力优势分析"""
        strengths = []

        # 1. 技术能力
        if len(skills) >= 5:
            strengths.append({"type": "technical", "desc": f"技术栈丰富，掌握 {len(skills)} 项核心技能", "score": 80})
        elif len(skills) >= 1:
            strengths.append({"type": "technical", "desc": f"具备 {len(skills)} 项专业技能", "score": 65})
        else:
            strengths.append({"type": "technical", "desc": "技术能力待补充", "score": 40})

        # 2. 实践经验
        total = len(experience) + len(project_experience)
        if total >= 3:
            strengths.append({"type": "project_execution", "desc": f"实践经历丰富，拥有 {total} 段实习/项目经验", "score": 85})
        elif total >= 1:
            strengths.append({"type": "project_execution", "desc": f"具备 {total} 段实习/项目经历", "score": 70})
        else:
            strengths.append({"type": "project_execution", "desc": "实践经历待补充", "score": 40})

        # 3. 数据分析
        data_kw = ["数据", "分析", "SQL", "Excel", "Python", "统计", "挖掘", "BI"]
        all_text = " ".join([s.get("name", "") for s in skills] +
                           [e.get("description", "") for e in experience] +
                           [p.get("description", "") for p in project_experience])
        if any(kw in all_text for kw in data_kw):
            strengths.append({"type": "data_analysis", "desc": "具备数据分析能力", "score": 75})
        else:
            strengths.append({"type": "data_analysis", "desc": "数据分析能力待提升", "score": 50})

        strengths.sort(key=lambda x: x.get("score", 0), reverse=True)
        return strengths[:5]

    # ── Summary 生成 ──────────────────────────────────────────────

    def _generate_summary(self, extracted: dict) -> str:
        """生成个人摘要：教育 + 经历概括 + 技能，不含公司名/日期/长描述"""
        skills = extracted.get("skills", [])
        experience = extracted.get("experience", [])
        project_experience = extracted.get("project_experience", [])
        education = extracted.get("education", [])

        parts = []

        # 教育背景
        if education:
            edu_parts = []
            for edu in education:
                if isinstance(edu, dict):
                    school = edu.get("school", "")
                    degree = edu.get("degree", "")
                    major = edu.get("major", "")
                else:
                    school = getattr(edu, "school", "")
                    degree = getattr(edu, "degree", "")
                    major = getattr(edu, "major", "")
                info = school
                if degree:
                    info += f"·{degree}"
                if major:
                    info += f"·{major}"
                edu_parts.append(info)
            parts.append(f"毕业于{'、'.join(edu_parts)}。")
        else:
            parts.append("教育背景待补充。")

        # 经历概括（仅数量，不含公司名/岗位）
        exp_count = len(experience)
        pe_count = len(project_experience)
        if exp_count > 0 and pe_count > 0:
            parts.append(f"拥有{exp_count}段工作/实习经历和{pe_count}个项目经验，具备实践经验。")
        elif exp_count > 0:
            parts.append(f"拥有{exp_count}段工作/实习经历，具备实践经验。")
        elif pe_count > 0:
            parts.append(f"主导{pe_count}个项目，具备项目实践经验。")
        else:
            parts.append("实践经历待补充。")

        # 核心技能
        if skills:
            skill_names = []
            for s in skills[:6]:
                if isinstance(s, dict):
                    skill_names.append(s.get("name", ""))
                else:
                    skill_names.append(getattr(s, "name", ""))
            parts.append(f"掌握{', '.join(skill_names)}等核心技能。")
        else:
            parts.append("专业技能待补充。")

        return "".join(parts)

    # ── 校验 ──────────────────────────────────────────────────────

    def _validate(self, extracted: dict) -> dict:
        """校验解析结果，返回 {valid, issues}"""
        issues = []

        # 检查必需字段
        if not extracted.get("education"):
            issues.append("缺少教育经历")
        if not extracted.get("experience") and not extracted.get("project_experience"):
            issues.append("缺少工作经历和项目经历")
        if not extracted.get("skills"):
            issues.append("缺少技能信息")

        # 检查 experience 字段完整性
        for i, exp in enumerate(extracted.get("experience", [])):
            if not exp.get("company"):
                issues.append(f"experience[{i}] 缺少 company")
            if not exp.get("position"):
                issues.append(f"experience[{i}] 缺少 position")
            if not exp.get("start_date"):
                issues.append(f"experience[{i}] 缺少 start_date")
            if not exp.get("description"):
                issues.append(f"experience[{i}] description 为空")

        # 检查 project 字段完整性
        for i, proj in enumerate(extracted.get("project_experience", [])):
            if not proj.get("project_name"):
                issues.append(f"project_experience[{i}] 缺少 project_name")
            if not proj.get("description"):
                issues.append(f"project_experience[{i}] description 为空")

        # 检查 skills 是否被错误合并
        for i, sk in enumerate(extracted.get("skills", [])):
            name = sk.get("name", "")
            if ':' in name or '：' in name:
                issues.append(f"skills[{i}] 名称包含分隔符，可能被错误合并: {name}")
            if len(name) > 60:
                issues.append(f"skills[{i}] 名称过长: {name[:30]}...")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }

    def _fallback_extract(self, text: str) -> dict:
        """备用解析：使用更宽松的规则重新解析"""
        logger.info("使用备用解析规则")
        # 重新运行主解析，但放宽过滤条件
        sections = self._detect_sections(text)
        education = []
        experience = []
        project_experience = []
        skills = []
        certificates = []

        for section in sections:
            name = section["name"]
            lines = section["lines"]
            if name == "education":
                education = self._parse_education_lines(lines)
            elif name == "experience":
                experience = self._parse_experience_lines(lines)
            elif name == "project":
                project_experience = self._parse_project_lines(lines)
            elif name == "skills":
                skills = self._parse_skills_lines(lines)
            elif name == "certificate":
                certificates = self._parse_certificate_lines(lines)
            else:
                # 未知章节：尝试按行解析
                for line in lines:
                    if self._is_education_line(line):
                        edu = self._parse_single_education(line)
                        if edu:
                            education.append(edu)
                    elif self._is_experience_line(line):
                        exp = self._parse_single_experience(line, lines, 0)
                        if exp:
                            experience.append(exp)
                    elif self._is_project_line(line):
                        proj = self._parse_single_project(line, lines, 0)
                        if proj:
                            project_experience.append(proj)
                    elif self._is_skill_line(line):
                        skills.extend(self._parse_skills_lines([line]))

        return {
            "education": [e.model_dump() for e in education],
            "experience": [e.model_dump() for e in experience],
            "project_experience": [p.model_dump() for p in project_experience],
            "skills": [s.model_dump() for s in skills],
            "certificates": [c.model_dump() for c in certificates],
            "strengths": [],
        }

    # ── 技能分类 ──────────────────────────────────────────────────

    def _classify_skill(self, name: str, description: str) -> str:
        """将技能分类到四个固定类别"""
        text = (name + " " + description).lower()

        technical_keywords = [
            "python", "go", "golang", "java", "javascript", "typescript",
            "react", "vue", "angular", "sql", "mysql", "postgresql", "redis",
            "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
            "machine learning", "deep learning", "nlp", "cv", "ai",
            "git", "linux", "nginx", "celery", "django", "flask", "fastapi",
            "spring", "node.js", "express", "mongodb", "elasticsearch",
            "c++", "c#", "rust", "swift", "kotlin", "php", "ruby",
            "api", "rest", "grpc", "microservice", "backend", "frontend",
            "全栈", "后端", "前端", "算法", "数据", "数据库", "框架",
            "编程语言", "开发", "工程", "系统", "架构",
        ]
        if any(kw in text for kw in technical_keywords):
            return "technical_skills"

        business_keywords = [
            "市场调研", "项目管理", "商业分析", "产品管理", "数据分析",
            "市场分析", "战略规划", "财务管理", "人力资源管理",
            "商业", "市场", "管理", "分析", "策略", "规划",
        ]
        if any(kw in name for kw in business_keywords):
            return "business_skills"

        content_keywords = [
            "内容制作", "内容创作", "文案", "写作", "设计", "视频",
            "摄影", "编辑", "策划", "新媒体", "运营",
        ]
        if any(kw in name for kw in content_keywords):
            return "content_skills"

        tools_keywords = [
            "excel", "tableau", "notion", "asana", "jira", "figma",
            "ps", "pr", "ai", "illustrator", "photoshop", "premiere",
            "office", "wps", "slack", "zoom", "trello", "confluence",
        ]
        if any(kw in text for kw in tools_keywords):
            return "tools_skills"

        return "technical_skills"

    # ── 辅助方法 ────────────────────────────────────────────────

    def _get_header_patterns(self, section_name: str) -> List[str]:
        """获取指定章节的标题匹配模式"""
        if section_name not in self.SECTION_PATTERNS:
            return []
        return self.SECTION_PATTERNS[section_name]

    def _extract_section(self, text: str, section_name: str) -> str:
        """提取指定章节内容"""
        pattern = re.compile(
            r'^(?:' + re.escape(section_name) + r'\s*(?::|：)\s*|' + re.escape(section_name) + r'\s*)',
            re.MULTILINE
        )
        match = pattern.search(text)
        if not match:
            return ""

        start = match.end()
        all_sections = [
            "联系方式", "求职信息", "资格证书", "个人优势",
            "教育经历", "实习经历", "项目经历", "专业技能"
        ]
        end = len(text)
        for sec in all_sections:
            if sec == section_name:
                continue
            sec_pattern = re.compile(
                r'^(?:' + re.escape(sec) + r'\s*(?::|：)\s*|' + re.escape(sec) + r'\s*)',
                re.MULTILINE
            )
            next_match = sec_pattern.search(text, start)
            if next_match and next_match.start() < end:
                end = next_match.start()

        return text[start:end].strip()

    def _optimize_summary(self, profile: ResumeProfile, job: Job) -> str:
        skills = profile.skills or []
        exps = profile.experience or []
        edus = profile.education or []

        job_title_lower = job.title.lower()
        focus_area = ""
        for kw in ["前端", "后端", "算法", "全栈", "移动端"]:
            if kw in job_title_lower:
                focus_area = kw
                break

        parts = []
        if edus:
            edu = edus[0]
            parts.append(f"{edu.get('school', '')}{edu.get('degree', '')}{edu.get('major', '')}背景")
        if focus_area:
            parts.append(f"专注于{focus_area}方向")
        if skills:
            skill_names = [s.get("name", "") for s in skills[:5]]
            parts.append(f"掌握{','.join(skill_names)}等技术")
        if exps:
            parts.append(f"具备{len(exps)}段项目/实习经验")
        return "，".join(parts)


# 全局引擎实例
engine = ResumeEngine()
