"""
JobSourceEngine — 统一岗位数据源系统
支持多种招聘平台，MVP 使用 Mock 数据
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.db.models import Job, JobType, CompanyType, JobSourceType
from app.db.models import JobSource as JobSourceModel
# Import enum separately to avoid shadowing
import enum
class _JobSourceEnum(str, enum.Enum):
    MOCK = "mock"
    LIEPIN = "liepin"
    BOSS = "boss"
    LAGOU = "lagou"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY = "company"
from sqlalchemy import select
from app.db.database import get_db
from app.schemas.models import JobResponse
from app.agents.job_source_adapters import ADAPTER_REGISTRY, get_adapter


class JobSourceEngine:
    """统一岗位数据源引擎"""

    # Mock 岗位数据池（模拟多来源）
    MOCK_JOBS = [
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://jobs.bytedance.com/campus",
            "company": "字节跳动",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "后端开发工程师（校招）",
            "location": "北京",
            "locations": ["北京"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责推荐系统后端服务开发，使用 Go/Python 构建高并发分布式系统；
2. 参与推荐算法的工程化落地，优化推荐效果和系统性能；
3. 负责核心服务模块的设计与开发，保障系统高可用性和可扩展性；
4. 参与技术架构演进，推动服务治理、监控告警等基础设施建设；
5. 与算法、产品团队紧密协作，持续迭代优化推荐体验。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟练掌握 Go 或 Python 至少一门编程语言，具备扎实的编程基础；
3. 了解数据结构与算法，具备基本的系统设计能力；
4. 熟悉 MySQL、Redis 等常用数据库，了解分布式系统基本原理；
5. 有实习经验或实际项目经验者优先考虑。

【福利待遇】
1. 具有竞争力的薪酬（25-45K/月），股票期权；
2. 五险一金、补充商业保险、年度体检；
3. 弹性工作制，免费三餐、零食饮料；
4. 扁平化管理，技术氛围浓厚，成长空间大。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟练掌握 Go 或 Python 至少一门编程语言，具备扎实的编程基础",
                "了解数据结构与算法，具备基本的系统设计能力",
                "熟悉 MySQL、Redis 等常用数据库，了解分布式系统基本原理",
                "有实习经验或实际项目经验者优先考虑"
            ],
            "preferred_skills": ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"],
            "tags": ["大厂", "核心技术", "成长快", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "industry": "互联网",
            "job_category": "后端开发",
            "apply_url": "https://jobs.bytedance.com/campus",
            "job_url": "https://jobs.bytedance.com/campus",
            "apply_source": "company",
            "company_website": "https://www.bytedance.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.alibaba.com/campus",
            "company": "阿里巴巴",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "前端开发工程师（校招）",
            "location": "杭州",
            "locations": ["杭州"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 40, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责淘宝/天猫前端核心业务开发，使用 React 技术栈构建高质量用户界面；
2. 参与前端架构设计和性能优化，提升页面加载速度和用户体验；
3. 与后端、设计团队紧密协作，完成复杂业务场景的前端实现；
4. 推动前端工程化建设，制定开发规范和最佳实践；
5. 参与技术选型和工具链建设，持续提升研发效率。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟练掌握 React 前端框架，具备扎实的前端开发能力；
3. 熟悉 TypeScript，了解前端工程化工具（Webpack/Vite）；
4. 了解前端性能优化和跨浏览器兼容性处理；
5. 有实际项目经验或实习经验者优先。

【福利待遇】
1. 具有竞争力的薪酬（25-40K/月），股票期权；
2. 五险一金、补充商业保险、年度体检；
3. 弹性工作制，免费三餐、下午茶；
4. 技术氛围浓厚，定期技术分享和培训。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟练掌握 React 前端框架，具备扎实的前端开发能力",
                "熟悉 TypeScript，了解前端工程化工具（Webpack/Vite）",
                "了解前端性能优化和跨浏览器兼容性处理",
                "有实际项目经验或实习经验者优先"
            ],
            "preferred_skills": ["React", "TypeScript", "JavaScript", "CSS", "Webpack", "Node.js"],
            "tags": ["大厂", "核心业务", "技术栈先进", "校招", "春招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "spring",
            "industry": "互联网",
            "job_category": "前端开发",
            "apply_url": "https://careers.alibaba.com/campus",
            "job_url": "https://careers.alibaba.com/campus",
            "apply_source": "boss",
            "company_website": "https://www.alibaba.com",
            "application_method": "内推/网申",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.tencent.com/campus",
            "company": "腾讯",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "算法工程师（校招）",
            "location": "深圳",
            "locations": ["深圳"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 30, "max": 55, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责搜索/推荐算法的研发与优化，提升用户体验和商业化效果；
2. 参与大模型相关技术研究，包括排序模型、召回策略、多目标优化等；
3. 负责算法模型的工程化部署和性能优化，保障线上服务稳定性；
4. 与产品、工程团队紧密协作，推动算法能力落地到实际业务场景；
5. 跟踪业界前沿技术动态，持续探索新技术在搜索推荐领域的应用。

【任职要求】
1. 硕士及以上学历，计算机、数学、统计等相关专业；
2. 扎实的数学基础，熟悉机器学习/深度学习算法原理；
3. 熟练掌握 Python/C++，熟悉 PyTorch/TensorFlow 等主流框架；
4. 有顶会论文（NeurIPS/ICML/KDD/SIGIR 等）者优先考虑；
5. 具备良好的英文文献阅读能力和技术沟通能力。

【福利待遇】
1. 顶级薪酬（30-55K/月），股票期权，年终奖；
2. 五险一金、补充商业保险、年度体检；
3. 弹性工作制，免费三餐、健身房；
4. 顶尖技术团队，参与行业前沿项目。""",
            "requirements": [
                "硕士及以上学历，计算机、数学、统计等相关专业",
                "扎实的数学基础，熟悉机器学习/深度学习算法原理",
                "熟练掌握 Python/C++，熟悉 PyTorch/TensorFlow 等主流框架",
                "有顶会论文（NeurIPS/ICML/KDD/SIGIR 等）者优先考虑",
                "具备良好的英文文献阅读能力和技术沟通能力"
            ],
            "preferred_skills": ["Python", "TensorFlow", "PyTorch", "NLP", "推荐系统", "C++"],
            "tags": ["大厂", "算法", "高薪资", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "industry": "互联网",
            "job_category": "算法工程",
            "apply_url": "https://careers.tencent.com/campus",
            "job_url": "https://careers.tencent.com/campus",
            "apply_source": "company",
            "company_website": "https://www.tencent.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://zhaopin.meituan.com/campus",
            "company": "美团",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "全栈开发工程师（校招）",
            "location": "北京",
            "locations": ["北京"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责本地生活服务平台全栈开发，覆盖 Web 端和移动端核心业务；
2. 参与前后端架构设计，推动技术选型和工程化建设；
3. 负责核心服务模块的开发，保障系统高可用性和性能；
4. 与产品、设计团队紧密协作，快速迭代业务功能；
5. 参与技术难题攻关，持续优化系统架构和开发效率。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟悉前端开发（Vue/React），了解后端开发（Node.js/Python）；
3. 了解数据库设计（PostgreSQL/MySQL），具备基本的系统设计能力；
4. 熟悉 Docker 容器化部署，了解 CI/CD 流程；
5. 有实际项目经验或实习经验者优先。

【福利待遇】
1. 具有竞争力的薪酬（25-45K/月），股票期权；
2. 五险一金、补充商业保险、年度体检；
3. 弹性工作制，免费三餐、零食饮料；
4. 技术氛围浓厚，成长空间大。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟悉前端开发（Vue/React），了解后端开发（Node.js/Python）",
                "了解数据库设计（PostgreSQL/MySQL），具备基本的系统设计能力",
                "熟悉 Docker 容器化部署，了解 CI/CD 流程",
                "有实际项目经验或实习经验者优先"
            ],
            "preferred_skills": ["Vue", "React", "Node.js", "Python", "PostgreSQL", "Docker"],
            "tags": ["大厂", "全栈", "业务丰富", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "industry": "互联网",
            "job_category": "移动端开发",
            "apply_url": "https://zhaopin.meituan.com/campus",
            "job_url": "https://zhaopin.meituan.com/campus",
            "apply_source": "boss",
            "company_website": "https://www.meituan.com",
            "application_method": "内推/网申",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.pinduoduo.com/campus",
            "company": "拼多多",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "移动端开发工程师（校招）",
            "location": "上海",
            "locations": ["上海"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 30, "max": 50, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责拼多多 App 核心功能开发，使用 Kotlin/Swift 构建高质量移动端体验；
2. 参与移动端架构设计和性能优化，提升 App 稳定性和用户体验；
3. 与后端、产品、设计团队紧密协作，快速迭代业务功能；
4. 负责移动端新技术调研和技术难题攻关；
5. 参与移动端工程化建设，推动开发效率和代码质量提升。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟悉 Android（Kotlin/Java）或 iOS（Swift/Objective-C）至少一端开发；
3. 了解移动端性能优化、内存管理和网络编程；
4. 熟悉跨平台开发框架（React Native/Flutter）者优先；
5. 有实际项目经验或实习经验者优先。

【福利待遇】
1. 具有竞争力的薪酬（30-50K/月），股票期权；
2. 五险一金、补充商业保险、年度体检；
3. 弹性工作制，免费三餐、下午茶；
4. 高速成长环境，参与亿级用户产品。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟悉 Android（Kotlin/Java）或 iOS（Swift/Objective-C）至少一端开发",
                "了解移动端性能优化、内存管理和网络编程",
                "熟悉跨平台开发框架（React Native/Flutter）者优先",
                "有实际项目经验或实习经验者优先"
            ],
            "preferred_skills": ["Kotlin", "Swift", "Java", "Objective-C", "React Native", "Flutter"],
            "tags": ["大厂", "移动端", "高并发", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "industry": "互联网",
            "job_category": "产品运营",
            "apply_url": "https://careers.pinduoduo.com/campus",
            "job_url": "https://careers.pinduoduo.com/campus",
            "apply_source": "company",
            "company_website": "https://www.pinduoduo.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "linkedin",
            "source_type": JobSourceType.LINKEDIN.value,
            "source_url": "https://careers.microsoft.com/campus",
            "company": "Microsoft",
            "company_type": CompanyType.FOREIGN.value,
            "company_country": "美国",
            "title": "Software Engineer I (校招)",
            "location": "北京",
            "locations": ["北京"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 40, "max": 70, "unit": "K/月"},
            "description": """【岗位职责】
1. 参与 Azure 云服务核心功能开发，使用 C#/Go 构建高可用分布式系统；
2. 负责云服务后端服务的设计、开发和优化，保障系统稳定性和性能；
3. 参与云原生技术栈建设，包括 Kubernetes、Service Mesh 等；
4. 与全球团队协作，参与技术架构评审和代码审查；
5. 跟踪云计算前沿技术，持续优化产品体验。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟练掌握至少一门编程语言（C#/Go/Java/Python）；
3. 了解分布式系统基本原理，具备基本的系统设计能力；
4. 具备良好的英语沟通能力，能够阅读英文技术文档；
5. 有实习经验或实际项目经验者优先。

【福利待遇】
1. 顶级薪酬（40-70K/月），股票期权，年终奖；
2. 完善的福利体系，补充商业保险、年度体检；
3. 工作生活平衡，弹性工作制，带薪年假；
4. 全球技术团队，国际化工作环境。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟练掌握至少一门编程语言（C#/Go/Java/Python）",
                "了解分布式系统基本原理，具备基本的系统设计能力",
                "具备良好的英语沟通能力，能够阅读英文技术文档",
                "有实习经验或实际项目经验者优先"
            ],
            "preferred_skills": ["C#", "Go", "Python", "Azure", "Kubernetes", "SQL"],
            "tags": ["外企", "WLB", "技术栈先进", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": True,
            "visa_support": True,
            "english_required": True,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "industry": "科技",
            "job_category": "后端开发",
            "apply_url": "https://careers.microsoft.com/campus",
            "job_url": "https://careers.microsoft.com/campus",
            "apply_source": "linkedin",
            "company_website": "https://www.microsoft.com",
            "application_method": "LinkedIn/官网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "linkedin",
            "source_type": JobSourceType.LINKEDIN.value,
            "source_url": "https://careers.google.com/jobs",
            "company": "Google",
            "company_type": CompanyType.FOREIGN.value,
            "company_country": "美国",
            "title": "Software Engineer - New Grad",
            "location": "上海",
            "locations": ["上海"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 50, "max": 80, "unit": "K/月"},
            "description": """【岗位职责】
1. 参与 Google Cloud 核心产品开发，使用 C++/Java 构建大规模分布式系统；
2. 负责云服务后端服务的设计、开发和性能优化；
3. 参与云原生技术栈建设，包括 Kubernetes、Cloud Spanner 等；
4. 与全球顶尖工程师协作，参与技术架构评审和代码审查；
5. 跟踪云计算和分布式系统前沿技术，持续推动技术创新。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 扎实的算法和数据结构基础，能够解决复杂技术问题；
3. 熟练掌握 C++/Java/Python 至少一门编程语言；
4. 具备良好的英语沟通能力，能够进行技术文档撰写和团队沟通；
5. 有实习经验或实际项目经验者优先。

【福利待遇】
1. 顶级薪酬（50-80K/月），股票期权，年终奖；
2. 完善的福利体系，补充商业保险、年度体检；
3. 工作生活平衡，弹性工作制，带薪年假；
4. 全球顶尖技术团队，参与行业前沿项目。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "扎实的算法和数据结构基础，能够解决复杂技术问题",
                "熟练掌握 C++/Java/Python 至少一门编程语言",
                "具备良好的英语沟通能力，能够进行技术文档撰写和团队沟通",
                "有实习经验或实际项目经验者优先"
            ],
            "preferred_skills": ["C++", "Java", "Python", "Go", "Distributed Systems", "Cloud"],
            "tags": ["外企", "顶级薪资", "技术挑战", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": True,
            "visa_support": True,
            "english_required": True,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "industry": "科技",
            "job_category": "前端开发",
            "apply_url": "https://careers.google.com/jobs",
            "job_url": "https://careers.google.com/jobs",
            "apply_source": "linkedin",
            "company_website": "https://www.google.com",
            "application_method": "官网申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "lagou",
            "source_type": JobSourceType.LAGOU.value,
            "source_url": "https://www.lagou.com/jobs/ai-startup",
            "company": "某AI创业公司",
            "company_type": CompanyType.STARTUP.value,
            "company_country": "中国",
            "title": "后端开发工程师（校招）",
            "location": "北京",
            "locations": ["北京"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 20, "max": 35, "unit": "K/月"},
            "description": """【岗位职责】
1. 参与 AI 产品后端开发，使用 Python/Go 构建大模型应用服务；
2. 负责 LLM 应用层开发，包括 RAG、Agent、Prompt Engineering 等；
3. 参与后端服务架构设计和性能优化，保障系统高可用性；
4. 与算法、产品团队紧密协作，推动 AI 能力落地到实际业务场景；
5. 跟踪 AI 领域前沿技术动态，持续探索新技术应用。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟练掌握 Python 或 Go 编程语言，具备扎实的编程基础；
3. 了解大语言模型（LLM）相关技术，有 LangChain/LlamaIndex 经验者优先；
4. 熟悉常用数据库（Redis/PostgreSQL），了解分布式系统基本原理；
5. 对 AI/LLM 领域有浓厚兴趣，具备快速学习能力。

【福利待遇】
1. 具有竞争力的薪酬（20-35K/月），股票期权；
2. 五险一金、年度体检；
3. 弹性工作制，扁平化管理；
4. 参与前沿 AI 项目，技术成长空间大。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟练掌握 Python 或 Go 编程语言，具备扎实的编程基础",
                "了解大语言模型（LLM）相关技术，有 LangChain/LlamaIndex 经验者优先",
                "熟悉常用数据库（Redis/PostgreSQL），了解分布式系统基本原理",
                "对 AI/LLM 领域有浓厚兴趣，具备快速学习能力"
            ],
            "preferred_skills": ["Python", "FastAPI", "LangChain", "Redis", "PostgreSQL", "Docker"],
            "tags": ["创业公司", "AI", "成长空间大", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "industry": "人工智能",
            "job_category": "算法工程",
            "apply_url": "https://www.lagou.com/jobs/ai-startup",
            "job_url": "https://www.lagou.com/jobs/ai-startup",
            "apply_source": "lagou",
            "company_website": "https://www.ai-startup.com",
            "application_method": "拉勾网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "liepin",
            "source_type": JobSourceType.LIEPIN.value,
            "source_url": "https://www.liepin.com/state-enterprise",
            "company": "某国企",
            "company_type": CompanyType.STATE_ENTERPRISE.value,
            "company_country": "中国",
            "title": "信息技术岗（校招）",
            "location": "北京",
            "locations": ["北京"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 15, "max": 25, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责企业内部信息系统（OA/ERP/HR 等）的开发与维护；
2. 参与信息化项目的需求分析、方案设计和实施管理；
3. 负责系统日常运维，保障系统稳定运行和数据安全；
4. 协助推进数字化转型项目，提升企业运营效率；
5. 参与技术架构演进，推动系统现代化改造。

【任职要求】
1. 本科及以上学历，计算机相关专业，2025 届校招优先；
2. 熟悉 Java/Python 至少一门后端编程语言；
3. 了解数据库（MySQL/PostgreSQL）和基本 SQL 操作；
4. 熟悉 Linux 操作系统，具备基本的命令行操作能力；
5. 了解 Vue 等前端框架者优先；
6. 稳定性要求高，具备良好的责任心和团队协作精神。

【福利待遇】
1. 具有竞争力的薪酬（15-25K/月）；
2. 五险一金、补充商业保险、年度体检；
3. 工作稳定，WLB 好，双休法定节假日；
4. 完善的培训体系，职业发展通道清晰。""",
            "requirements": [
                "本科及以上学历，计算机相关专业，2025 届校招优先",
                "熟悉 Java/Python 至少一门后端编程语言",
                "了解数据库（MySQL/PostgreSQL）和基本 SQL 操作",
                "熟悉 Linux 操作系统，具备基本的命令行操作能力",
                "了解 Vue 等前端框架者优先",
                "稳定性要求高，具备良好的责任心和团队协作精神"
            ],
            "preferred_skills": ["Java", "Spring Boot", "MySQL", "Vue", "Linux"],
            "tags": ["国企", "稳定", "WLB好", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "industry": "金融",
            "job_category": "数据分析",
            "apply_url": "https://www.liepin.com/state-enterprise",
            "job_url": "https://www.liepin.com/state-enterprise",
            "apply_source": "liepin",
            "company_website": "https://www.state-enterprise.com",
            "application_method": "猎聘/官网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "boss",
            "source_type": JobSourceType.BOSS.value,
            "source_url": "https://www.wechatjobs.com/remote",
            "company": "某远程公司",
            "company_type": CompanyType.STARTUP.value,
            "company_country": "美国",
            "title": "前端开发工程师（远程）",
            "location": "远程",
            "locations": ["Remote"],
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 20, "max": 40, "unit": "K/月"},
            "description": """【岗位职责】
1. 负责 SaaS 产品前端开发，使用 React/TypeScript 构建高质量用户界面；
2. 参与前端架构设计和技术选型，推动前端工程化建设；
3. 优化前端性能，提升用户体验和页面加载速度；
4. 与后端、设计团队紧密协作，完成产品功能迭代；
5. 参与远程团队协作，遵循敏捷开发流程。

【任职要求】
1. 本科及以上学历，计算机相关专业；
2. 熟练掌握 React 和 TypeScript，具备扎实的前端开发能力；
3. 熟悉 Next.js 框架，了解 SSR/SSG 原理；
4. 了解 Tailwind CSS 等现代 CSS 框架，具备优秀的 UI 实现能力；
5. 具备良好的英语沟通能力，能够进行技术文档撰写和团队沟通；
6. 有独立开发能力和远程协作经验者加分。

【福利待遇】
1. 具有竞争力的薪酬（20-40K/月）；
2. 完全远程办公，灵活工作时间；
3. 国际化团队，接触前沿技术栈；
4. 股票期权，参与公司成长红利。""",
            "requirements": [
                "本科及以上学历，计算机相关专业",
                "熟练掌握 React 和 TypeScript，具备扎实的前端开发能力",
                "熟悉 Next.js 框架，了解 SSR/SSG 原理",
                "了解 Tailwind CSS 等现代 CSS 框架，具备优秀的 UI 实现能力",
                "具备良好的英语沟通能力，能够进行技术文档撰写和团队沟通",
                "有独立开发能力和远程协作经验者加分"
            ],
            "preferred_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "GraphQL"],
            "tags": ["远程", "灵活", "国际化", "海外机会"],
            "is_remote": True,
            "is_foreign": False,
            "visa_support": False,
            "english_required": True,
            "graduate_program": False,
            "campus_recruitment": False,
            "season": "regular",
            "industry": "远程工作",
            "job_category": "全栈开发",
            "apply_url": "https://www.wechatjobs.com/remote",
            "job_url": "https://www.wechatjobs.com/remote",
            "apply_source": "boss",
            "company_website": "https://www.remote-company.com",
            "application_method": "微信/官网",
        },
    ]

    async def seed_mock_jobs(self) -> List[JobResponse]:
        """初始化/更新 Mock 岗位数据（upsert：存在则更新，不存在则新增）"""
        async for db in get_db():
            added = 0
            updated = 0
            for data in self.MOCK_JOBS:
                # 按 source + title 判断是否已存在（可能有同名岗位，取第一个）
                existing = await db.execute(
                    select(Job).where(
                        Job.source == data["source"],
                        Job.title == data["title"],
                    ).limit(1)
                )
                job = existing.scalar_one_or_none()

                if job:
                    # 更新关键字段
                    job.description = data["description"]
                    job.requirements = data["requirements"]
                    job.preferred_skills = data["preferred_skills"]
                    job.tags = data["tags"]
                    # 更新 locations（标准化地点列表）
                    if "locations" in data:
                        job.locations = data["locations"]
                    updated += 1
                else:
                    # 新增
                    job_id = str(uuid.uuid4())
                    job = Job(id=job_id, **data)
                    db.add(job)
                    added += 1

            await db.commit()
            logger.info(f"Mock 岗位数据: 新增 {added} 条, 更新 {updated} 条")
            # 返回数据库中实际更新的记录
            result = await db.execute(select(Job).where(Job.source == data["source"]))
            return [JobResponse.model_validate(j) for j in result.scalars().all()]

    async def search_jobs(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        locations: Optional[str] = None,  # 逗号分隔的多地点
        job_type: Optional[str] = None,
        company_type: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        salary_ranges: Optional[str] = None,  # 薪资范围，如 "20-30,30-50"
        is_foreign: Optional[bool] = None,
        is_remote: Optional[str] = None,
        has_apply_url: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        company_country: Optional[str] = None,
        visa_support: Optional[bool] = None,
        english_required: Optional[bool] = None,
        graduate_program: Optional[bool] = None,
        campus_recruitment: Optional[bool] = None,
        season: Optional[str] = None,
        industry: Optional[str] = None,  # 行业筛选（逗号分隔）
        job_category: Optional[str] = None,  # 岗位分类筛选（逗号分隔）
        status: Optional[str] = None,  # 岗位状态筛选
        limit: int = 20,
        offset: int = 0,
    ) -> List[JobResponse]:
        """搜索岗位（支持多维度筛选）"""
        async for db in get_db():
            query = select(Job)

            # 默认只展示 ACTIVE 岗位
            if status is None:
                query = query.where(Job.status == "active")
            else:
                query = query.where(Job.status == status)

            if keyword:
                kw = keyword.lower()
                query = query.where(
                    (Job.title.ilike(f"%{kw}%")) |
                    (Job.company.ilike(f"%{kw}%")) |
                    (Job.description.ilike(f"%{kw}%"))
                )
            if location:
                query = query.where(Job.location.ilike(f"%{location}%"))
            if locations:
                # 多地点筛选：任意地点命中即可（OR 逻辑）
                loc_list = [l.strip() for l in locations.split(",") if l.strip()]
                if loc_list:
                    from sqlalchemy import or_
                    location_conditions = [Job.locations.contains([loc]) for loc in loc_list]
                    query = query.where(or_(*location_conditions))
            if job_type:
                query = query.where(Job.job_type == job_type)
            if company_type:
                query = query.where(Job.company_type == company_type)
            if is_foreign is not None:
                query = query.where(Job.is_foreign == is_foreign)
            if is_remote is not None:
                query = query.where(Job.is_remote == is_remote)
            if has_apply_url is not None:
                if has_apply_url:
                    query = query.where(Job.apply_url.isnot(None))
                else:
                    query = query.where(Job.apply_url.is_(None))
            if salary_min is not None:
                query = query.where(Job.salary_range["min"].as_integer() >= salary_min)
            if salary_max is not None:
                query = query.where(Job.salary_range["max"].as_integer() <= salary_max)
            if salary_ranges:
                # 多薪资范围筛选：任意范围命中即可（OR 逻辑）
                range_list = [r.strip() for r in salary_ranges.split(",") if r.strip()]
                if range_list:
                    from sqlalchemy import or_
                    salary_conditions = []
                    for range_str in range_list:
                        if '-' in range_str:
                            parts = range_str.split('-')
                            if len(parts) == 2:
                                try:
                                    min_val = float(parts[0])
                                    max_val = float(parts[1])
                                    salary_conditions.append(
                                        (Job.salary_range["min"].as_integer() >= min_val) &
                                        (Job.salary_range["max"].as_integer() <= max_val)
                                    )
                                except ValueError:
                                    pass
                        elif range_str.endswith('+'):
                            try:
                                min_val = float(range_str[:-1])
                                salary_conditions.append(
                                    Job.salary_range["min"].as_integer() >= min_val
                                )
                            except ValueError:
                                pass
                    if salary_conditions:
                        query = query.where(or_(*salary_conditions))
            if tags:
                for tag in tags:
                    query = query.where(Job.tags.contains([tag]))
            if source_type:
                query = query.where(Job.source_type == source_type)
            if company_country:
                query = query.where(Job.company_country.ilike(f"%{company_country}%"))
            if visa_support is not None:
                query = query.where(Job.visa_support == visa_support)
            if english_required is not None:
                query = query.where(Job.english_required == english_required)
            if graduate_program is not None:
                query = query.where(Job.graduate_program == graduate_program)
            if campus_recruitment is not None:
                query = query.where(Job.campus_recruitment == campus_recruitment)
            if season:
                query = query.where(Job.season == season)
            if industry:
                # 多行业筛选：任意行业命中即可（OR 逻辑）
                industry_list = [i.strip() for i in industry.split(",") if i.strip()]
                if industry_list:
                    from sqlalchemy import or_
                    industry_conditions = [Job.industry == ind for ind in industry_list]
                    query = query.where(or_(*industry_conditions))
            if job_category:
                # 多岗位分类筛选：任意分类命中即可（OR 逻辑）
                category_list = [c.strip() for c in job_category.split(",") if c.strip()]
                if category_list:
                    from sqlalchemy import or_
                    category_conditions = [Job.job_category == cat for cat in category_list]
                    query = query.where(or_(*category_conditions))

            result = await db.execute(query.offset(offset).limit(limit))
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        async for db in get_db():
            job = await db.get(Job, job_id)
            if job:
                return JobResponse.model_validate(job)
        return None

    async def get_foreign_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取外企岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.is_foreign == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_campus_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取校招岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.campus_recruitment == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_remote_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取远程岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.is_remote == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_overseas_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取海外岗位（外企+远程+签证支持）"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(
                    (Job.is_foreign == True) |
                    (Job.is_remote == True) |
                    (Job.visa_support == True)
                )
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def sync_source_jobs(
        self,
        source_name: str,
        keyword: str = "",
        location: str = "",
        limit: int = 20
    ) -> Dict[str, Any]:
        """同步指定数据源的岗位数据"""
        from app.db.models import Job
        import uuid as uuid_module

        adapter = get_adapter(source_name)
        if not adapter:
            logger.error(f"[JobSync] 数据源不存在: {source_name}")
            return {"source": source_name, "added": 0, "updated": 0, "jobs": []}

        logger.info(f"[JobSync] 开始同步 source={source_name}, keyword={keyword}, location={location}")

        # 获取岗位列表
        raw_jobs = await adapter.fetch_jobs(keyword, location, limit)
        if not raw_jobs:
            logger.info(f"[JobSync] source={source_name} 未获取到岗位")
            return {"source": source_name, "added": 0, "updated": 0, "jobs": []}

        # 标准化岗位数据
        normalized_jobs = []
        for raw_job in raw_jobs:
            # 判断是否是 GreenhouseSource
            if source_name == "greenhouse":
                from app.agents.sources.greenhouse_source import GreenhouseSource
                if isinstance(adapter, GreenhouseSource):
                    normalized = adapter.normalize_greenhouse_job(raw_job)
                else:
                    normalized = adapter.normalize_job(raw_job)
            else:
                normalized = adapter.normalize_job(raw_job)
            normalized_jobs.append(normalized)

        # 保存到数据库
        added = 0
        updated = 0
        saved_jobs = []

        async for db in get_db():
            for job_data in normalized_jobs:
                source_job_id = job_data.get("source_job_id", "")
                title = job_data.get("title", "")
                company = job_data.get("company", "")

                # 检查是否已存在
                existing = None
                if source_job_id:
                    existing = await db.execute(
                        select(Job).where(Job.source_job_id == source_job_id).limit(1)
                    )
                    existing = existing.scalar_one_or_none()

                if not existing:
                    # 按 source + title + company 判断
                    existing = await db.execute(
                        select(Job).where(
                            Job.source == job_data.get("source", ""),
                            Job.title == title,
                            Job.company == company,
                        ).limit(1)
                    )
                    existing = existing.scalar_one_or_none()

                if existing:
                    # 更新
                    for key, value in job_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.updated_time = datetime.utcnow()
                    updated += 1
                    logger.info(f"[JobSync] updated=1 title={title}")
                    saved_jobs.append(JobResponse.model_validate(existing))
                else:
                    # 新增
                    job_id = str(uuid_module.uuid4())
                    job_data["id"] = job_id
                    job_data["created_at"] = datetime.utcnow()
                    job_data["updated_time"] = datetime.utcnow()
                    try:
                        job = Job(**job_data)
                    except Exception as e:
                        logger.error(f"[JobSync] Job 创建失败: {e}")
                        logger.error(f"[JobSync] job_data: {job_data}")
                        continue
                    db.add(job)
                    added += 1
                    logger.info(f"[JobSync] added=1 title={title}")
                    saved_jobs.append(JobResponse.model_validate(job))

            await db.commit()

        logger.info(f"[JobSync] source={source_name} added={added} updated={updated}")

        return {
            "source": source_name,
            "added": added,
            "updated": updated,
            "jobs": saved_jobs,
        }
