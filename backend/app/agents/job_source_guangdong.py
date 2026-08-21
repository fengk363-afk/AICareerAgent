"""
广东岗位采集模块 — 第一阶段
支持：广东人才网 (gdrc) + 广东公共招聘平台 (gd_public)
MVP 使用结构化 Mock 数据模拟接口层，后续替换为真实爬虫/API
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter, ADAPTER_REGISTRY


# ── 广东人才网 Mock 数据 ──────────────────────────────────────

_GDRC_JOBS = [
    {
        "source_job_id": "gdrc_001",
        "company": "广东省科学院智能信息研究所",
        "company_type": "state_enterprise",
        "title": "人工智能算法工程师",
        "location": "广州",
        "locations": ["广州"],
        "job_type": "full_time",
        "salary_range": {"min": 18, "max": 30, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责智能信息处理、自然语言处理、计算机视觉等方向的核心算法研发与落地应用；
2. 参与大语言模型（LLM）相关技术研究，包括预训练、微调、RAG 检索增强生成等方向；
3. 负责算法模型的工程化部署，优化推理性能，提升系统响应速度和稳定性；
4. 与产品、工程团队紧密协作，将算法能力转化为实际业务解决方案；
5. 跟踪 AI 领域前沿技术动态，持续优化算法方案，提升系统智能化水平。

【任职要求】
1. 硕士及以上学历，计算机、人工智能、数学、电子信息等相关专业；
2. 熟练掌握 Python/C++ 编程语言，具备扎实的编程基础和代码规范意识；
3. 熟悉主流深度学习框架（PyTorch/TensorFlow），有 NLP 或 CV 方向项目经验者优先；
4. 了解大语言模型相关技术，有 LLM 微调、Prompt Engineering 实践经验者加分；
5. 具备良好的英文文献阅读能力，能够跟踪国际前沿研究成果；
6. 具有较强的问题分析能力和团队协作精神，责任心强。

【福利待遇】
1. 具有竞争力的薪酬待遇（18-30K/月），年终奖金；
2. 五险一金、补充医疗保险、年度体检；
3. 弹性工作制，双休，法定节假日正常休息；
4. 完善的培训体系，提供学术交流、技术培训机会；
5. 良好的科研氛围，参与省级重点科研项目。""",
        "requirements": [
            "硕士及以上学历，计算机、人工智能、数学、电子信息等相关专业",
            "熟练掌握 Python/C++ 编程语言，具备扎实的编程基础",
            "熟悉主流深度学习框架（PyTorch/TensorFlow），有 NLP 或 CV 项目经验者优先",
            "了解大语言模型相关技术，有 LLM 微调、RAG 实践经验者加分",
            "具备良好的英文文献阅读能力",
            "具有较强的问题分析能力和团队协作精神"
        ],
        "preferred_skills": ["Python", "PyTorch", "NLP", "Transformer", "Linux", "LLM", "RAG"],
        "tags": ["国企", "科研", "AI", "广州", "算法", "大模型"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=3),
        "apply_url": "https://www.gdrc.com/job/gdrc_001",
        "job_url": "https://www.gdrc.com/job/gdrc_001",
        "company_website": "https://www.gdasi.cn",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_002",
        "company": "广州市人民政府办公厅",
        "company_type": "government",
        "title": "信息化管理岗（公务员）",
        "location": "广州",
        "locations": ["广州"],
        "job_type": "full_time",
        "salary_range": {"min": 10, "max": 18, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责市政府信息化系统的规划、建设、运维和管理，推进数字政府建设；
2. 参与政务信息化项目的需求分析、方案设计和实施管理；
3. 负责政务数据资源的整合与共享，推动数据开放和应用；
4. 参与网络安全体系建设，保障政务信息系统安全稳定运行；
5. 协助开展信息化相关政策的调研和制定工作。

【任职要求】
1. 本科及以上学历，计算机科学与技术、软件工程、信息管理等相关专业；
2. 熟悉信息系统项目管理流程，具备一定的项目管理能力；
3. 了解政务信息化相关政策和标准规范；
4. 具备良好的沟通协调能力和服务意识；
5. 中共党员优先，有政府信息化工作经验者优先。

【福利待遇】
1. 公务员编制，享受国家规定的公务员福利待遇；
2. 稳定的工作环境，完善的社会保障；
3. 定期培训，职业发展通道清晰。""",
        "requirements": [
            "本科及以上学历，计算机科学与技术、软件工程、信息管理等相关专业",
            "熟悉信息系统项目管理流程，具备一定的项目管理能力",
            "了解政务信息化相关政策和标准规范",
            "具备良好的沟通协调能力和服务意识",
            "中共党员优先，有政府信息化工作经验者优先"
        ],
        "preferred_skills": ["Java", "MySQL", "Linux", "网络安全", "项目管理"],
        "tags": ["公务员", "稳定", "广州", "信息化", "政府"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=7),
        "apply_url": "https://www.gdrc.com/job/gdrc_002",
        "job_url": "https://www.gdrc.com/job/gdrc_002",
        "company_website": "https://www.gz.gov.cn",
        "application_method": "广东人才网报名",
    },
    {
        "source_job_id": "gdrc_003",
        "company": "深圳技术大学",
        "company_type": "state_enterprise",
        "title": "前端开发工程师（校招）",
        "location": "深圳",
        "locations": ["深圳"],
        "job_type": "full_time",
        "salary_range": {"min": 15, "max": 25, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责学校智慧校园系统的前端开发工作，包括教务系统、办公系统、学生服务平台等；
2. 参与前端技术架构设计，制定前端开发规范和最佳实践；
3. 优化前端性能，提升用户体验，确保系统在不同终端上的良好展示；
4. 与后端开发、UI 设计团队紧密协作，完成功能模块的开发和上线；
5. 参与前端技术选型和工具链建设，推动前端工程化体系建设。

【任职要求】
1. 2025 届本科及以上学历，计算机、软件工程、信息管理等相关专业；
2. 熟练掌握 JavaScript/TypeScript，熟悉 Vue.js 或 React 前端框架；
3. 了解前端工程化工具（Webpack/Vite），具备一定的项目构建和优化经验；
4. 熟悉响应式设计和跨浏览器兼容性问题处理；
5. 具备良好的代码规范和文档编写习惯；
6. 有实际项目开发经验或实习经验者优先。

【福利待遇】
1. 高校编制或合同制，享受学校教职工相关福利；
2. 稳定的工作环境，寒暑假福利；
3. 完善的培训体系，提供技术成长空间。""",
        "requirements": [
            "2025 届本科及以上学历，计算机、软件工程、信息管理等相关专业",
            "熟练掌握 JavaScript/TypeScript，熟悉 Vue.js 或 React 前端框架",
            "了解前端工程化工具（Webpack/Vite）",
            "熟悉响应式设计和跨浏览器兼容性问题处理",
            "具备良好的代码规范和文档编写习惯",
            "有实际项目开发经验或实习经验者优先"
        ],
        "preferred_skills": ["Vue", "TypeScript", "JavaScript", "CSS", "Node.js", "Vite"],
        "tags": ["高校", "校招", "深圳", "前端", "智慧校园"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=1),
        "apply_url": "https://www.gdrc.com/job/gdrc_003",
        "job_url": "https://www.gdrc.com/job/gdrc_003",
        "company_website": "https://www.gdpu.edu.cn",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_004",
        "company": "珠海格力电器股份有限公司",
        "company_type": "state_enterprise",
        "title": "嵌入式软件工程师",
        "location": "珠海",
        "locations": ["珠海"],
        "job_type": "full_time",
        "salary_range": {"min": 16, "max": 28, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责家电产品嵌入式软件的设计、开发和调试工作；
2. 参与智能家电控制系统的架构设计和核心模块开发；
3. 负责嵌入式软件的代码编写、单元测试和集成测试；
4. 配合硬件团队完成软硬件联调，解决嵌入式系统中的技术问题；
5. 参与产品迭代优化，持续提升产品性能和用户体验。

【任职要求】
1. 本科及以上学历，电子工程、自动化、计算机、通信工程等相关专业；
2. 熟练掌握 C/C++ 编程语言，具备扎实的嵌入式开发基础；
3. 熟悉 ARM 架构嵌入式开发，了解常用外设驱动开发；
4. 了解实时操作系统（RTOS）或 Linux 嵌入式开发者优先；
5. 具备良好的问题分析能力和调试能力；
6. 有家电或物联网相关项目经验者优先。

【福利待遇】
1. 国企编制，具有竞争力的薪酬体系；
2. 五险一金、补充公积金、年度体检；
3. 员工宿舍、食堂补贴、节日福利；
4. 完善的培训体系，技术晋升通道清晰。""",
        "requirements": [
            "本科及以上学历，电子工程、自动化、计算机、通信工程等相关专业",
            "熟练掌握 C/C++ 编程语言，具备扎实的嵌入式开发基础",
            "熟悉 ARM 架构嵌入式开发，了解常用外设驱动开发",
            "了解实时操作系统（RTOS）或 Linux 嵌入式开发者优先",
            "具备良好的问题分析能力和调试能力",
            "有家电或物联网相关项目经验者优先"
        ],
        "preferred_skills": ["C", "C++", "嵌入式", "ARM", "Linux", "RTOS", "物联网"],
        "tags": ["国企", "制造业", "珠海", "嵌入式", "格力"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": True,
        "season": "autumn",
        "posted_at": datetime.utcnow() - timedelta(days=5),
        "apply_url": "https://www.gdrc.com/job/gdrc_004",
        "job_url": "https://www.gdrc.com/job/gdrc_004",
        "company_website": "https://www.gree.com",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_005",
        "company": "东莞松山湖高新技术产业开发区管委会",
        "company_type": "government",
        "title": "产业服务专员（校招）",
        "location": "东莞",
        "locations": ["东莞"],
        "job_type": "full_time",
        "salary_range": {"min": 8, "max": 14, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责园区企业的日常服务与管理工作，协助企业解决生产经营中的问题；
2. 参与招商引资工作，协助开展企业对接、项目洽谈等活动；
3. 负责产业政策的研究和解读，协助企业申报各类扶持项目；
4. 组织园区企业交流活动，搭建企业间合作平台；
5. 完成领导交办的其他工作任务。

【任职要求】
1. 2025 届本科及以上学历，经济管理、工商管理、理工科等相关专业；
2. 具备良好的公文写作能力和数据分析能力；
3. 熟练使用 Office 办公软件（Excel、PPT、Word）；
4. 具备良好的沟通协调能力和服务意识；
5. 性格开朗，责任心强，能够适应一定程度的出差；
6. 有学生会干部或社团工作经验者优先。

【福利待遇】
1. 政府平台编制，工作环境稳定；
2. 五险一金、带薪年假、节日福利；
3. 完善的培训体系，职业发展通道清晰；
4. 位于松山湖高新区，周边配套设施完善。""",
        "requirements": [
            "2025 届本科及以上学历，经济管理、工商管理、理工科等相关专业",
            "具备良好的公文写作能力和数据分析能力",
            "熟练使用 Office 办公软件（Excel、PPT、Word）",
            "具备良好的沟通协调能力和服务意识",
            "性格开朗，责任心强，能够适应一定程度的出差",
            "有学生会干部或社团工作经验者优先"
        ],
        "preferred_skills": ["数据分析", "公文写作", "Excel", "PPT", "沟通"],
        "tags": ["政府", "校招", "东莞", "产业服务", "松山湖"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=10),
        "apply_url": "https://www.gdrc.com/job/gdrc_005",
        "job_url": "https://www.gdrc.com/job/gdrc_005",
        "company_website": "https://www.songshanlake.gov.cn",
        "application_method": "广东人才网报名",
    },
]


# ── 广东公共招聘平台 Mock 数据 ────────────────────────────────

_GDPUBLIC_JOBS = [
    {
        "source_job_id": "gdpub_001",
        "company": "广东省人才交流服务中心",
        "company_type": "government",
        "title": "人力资源助理（劳务派遣）",
        "location": "广州",
        "locations": ["广州"],
        "job_type": "full_time",
        "salary_range": {"min": 6, "max": 10, "unit": "K/月"},
        "description": """【岗位职责】
1. 协助开展人才招聘工作，包括简历筛选、面试安排、入职办理等全流程支持；
2. 负责招聘渠道的日常维护，包括招聘网站信息更新、候选人沟通跟进；
3. 参与招聘活动的组织和执行，包括校园招聘、专场招聘会等；
4. 协助开展员工关系管理工作，包括劳动合同签订、档案管理等；
5. 完成上级交办的其他人力资源相关工作。

【任职要求】
1. 本科及以上学历，人力资源管理、行政管理、心理学等相关专业优先；
2. 熟悉招聘流程和面试技巧，具备良好的沟通表达能力；
3. 熟练使用 Office 办公软件，具备基本的文档处理能力；
4. 工作细致认真，具备良好的服务意识和团队协作精神；
5. 应届毕业生或 1 年以下相关工作经验均可。

【福利待遇】
1. 劳务派遣形式，享受用人单位提供的福利待遇；
2. 五险一金、周末双休、法定节假日；
3. 稳定的工作环境，位于广州市中心。""",
        "requirements": [
            "本科及以上学历，人力资源管理、行政管理、心理学等相关专业优先",
            "熟悉招聘流程和面试技巧，具备良好的沟通表达能力",
            "熟练使用 Office 办公软件，具备基本的文档处理能力",
            "工作细致认真，具备良好的服务意识和团队协作精神",
            "应届毕业生或 1 年以下相关工作经验均可"
        ],
        "preferred_skills": ["HR", "招聘", "Excel", "沟通", "面试"],
        "tags": ["政府", "人力资源", "广州", "稳定", "劳务派遣"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=2),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_001",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_001",
        "company_website": "https://gdreclruit.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_002",
        "company": "佛山市人力资源和社会保障局",
        "company_type": "government",
        "title": "就业服务专员（校招）",
        "location": "佛山",
        "locations": ["佛山"],
        "job_type": "full_time",
        "salary_range": {"min": 7, "max": 12, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责就业政策的宣传解读，向用人单位和求职者提供政策咨询服务；
2. 组织和管理各类招聘会活动，包括线上招聘会和线下专场招聘；
3. 开展失业登记和就业帮扶工作，协助困难群体实现就业；
4. 负责就业数据的统计分析和报表编制，为政策制定提供数据支撑；
5. 参与就业服务项目的策划和实施，提升公共就业服务质量。

【任职要求】
1. 2025 届本科及以上学历，公共管理、社会学、人力资源管理等相关专业优先；
2. 具备良好的文字表达能力和活动策划能力；
3. 熟悉办公软件操作，具备基本的数据分析能力；
4. 具有较强的责任心和服务意识，能够耐心解答群众咨询；
5. 中共党员优先，有学生会或社团工作经验者加分。

【福利待遇】
1. 政府事业单位编制，工作稳定有保障；
2. 五险一金、带薪年假、节日福利；
3. 完善的培训体系，职业发展通道清晰。""",
        "requirements": [
            "2025 届本科及以上学历，公共管理、社会学、人力资源管理等相关专业优先",
            "具备良好的文字表达能力和活动策划能力",
            "熟悉办公软件操作，具备基本的数据分析能力",
            "具有较强的责任心和服务意识，能够耐心解答群众咨询",
            "中共党员优先，有学生会或社团工作经验者加分"
        ],
        "preferred_skills": ["公文写作", "活动策划", "数据分析", "Excel", "PPT"],
        "tags": ["政府", "校招", "佛山", "就业服务", "事业单位"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=4),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_002",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_002",
        "company_website": "https://fslh.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_003",
        "company": "广州市公共就业服务中心",
        "company_type": "government",
        "title": "职业指导师",
        "location": "广州",
        "locations": ["广州"],
        "job_type": "full_time",
        "salary_range": {"min": 8, "max": 15, "unit": "K/月"},
        "description": """【岗位职责】
1. 为求职者提供职业规划咨询服务，帮助求职者明确职业发展方向；
2. 提供简历修改和面试指导服务，提升求职者就业竞争力；
3. 开展职业指导讲座和培训活动，普及就业知识和求职技巧；
4. 分析就业市场趋势和岗位需求，为求职者提供市场信息参考；
5. 建立和维护求职者档案，跟踪服务效果，持续优化服务质量。

【任职要求】
1. 本科及以上学历，心理学、人力资源管理、社会学等相关专业优先；
2. 有职业规划或 HR 相关经验者优先，持有职业指导师证书者加分；
3. 具备良好的沟通表达能力和倾听能力，能够耐心解答求职者疑问；
4. 熟悉就业市场动态和求职技巧，具备基本的简历分析和面试评估能力；
5. 具有较强的责任心和服务意识，愿意帮助求职者解决就业难题。

【福利待遇】
1. 政府事业单位编制，工作环境稳定；
2. 五险一金、带薪年假、节日福利；
3. 定期培训，提供职业能力提升机会。""",
        "requirements": [
            "本科及以上学历，心理学、人力资源管理、社会学等相关专业优先",
            "有职业规划或 HR 相关经验者优先，持有职业指导师证书者加分",
            "具备良好的沟通表达能力和倾听能力",
            "熟悉就业市场动态和求职技巧",
            "具有较强的责任心和服务意识"
        ],
        "preferred_skills": ["职业规划", "沟通", "简历优化", "面试辅导", "心理学"],
        "tags": ["政府", "职业指导", "广州", "公共服务", "事业单位"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=6),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_003",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_003",
        "company_website": "https://gzjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_004",
        "company": "深圳市公共就业服务平台",
        "company_type": "government",
        "title": "数据分析师（校招）",
        "location": "深圳",
        "locations": ["深圳"],
        "job_type": "full_time",
        "salary_range": {"min": 10, "max": 18, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责就业市场数据的采集、清洗和分析，生成就业市场分析报告；
2. 参与招聘趋势研究，分析岗位需求变化和行业人才流动情况；
3. 开发和维护数据分析报表和可视化看板，支撑管理决策；
4. 协助开展就业政策效果评估，为政策优化提供数据依据；
5. 参与就业服务平台的数据治理和质量管理相关工作。

【任职要求】
1. 2025 届本科及以上学历，统计学、计算机科学、经济学、数据科学等相关专业；
2. 熟练掌握 SQL 语言，能够独立完成数据查询和处理；
3. 熟悉 Python 数据分析工具（Pandas、NumPy），具备基本的数据处理能力；
4. 了解数据可视化工具（Tableau/Power BI/Echarts）者优先；
5. 具备良好的逻辑思维能力和数据分析意识，对数据敏感。

【福利待遇】
1. 政府平台编制，工作环境稳定；
2. 五险一金、带薪年假、节日福利；
3. 位于深圳市中心，交通便利，周边配套设施完善。""",
        "requirements": [
            "2025 届本科及以上学历，统计学、计算机科学、经济学、数据科学等相关专业",
            "熟练掌握 SQL 语言，能够独立完成数据查询和处理",
            "熟悉 Python 数据分析工具（Pandas、NumPy）",
            "了解数据可视化工具（Tableau/Power BI/Echarts）者优先",
            "具备良好的逻辑思维能力和数据分析意识"
        ],
        "preferred_skills": ["Python", "SQL", "数据分析", "Tableau", "Excel", "Pandas"],
        "tags": ["政府", "校招", "深圳", "数据分析", "公共就业"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=1),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_004",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_004",
        "company_website": "https://szjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_005",
        "company": "广东省就业服务中心",
        "company_type": "government",
        "title": "信息化运维工程师",
        "location": "广州",
        "locations": ["广州"],
        "job_type": "full_time",
        "salary_range": {"min": 9, "max": 16, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责省级就业服务平台的日常运维工作，保障系统稳定运行；
2. 及时处理系统故障和技术问题，确保服务连续性和数据安全性；
3. 参与系统监控和性能优化，持续提升系统运行效率；
4. 协助开展系统升级和功能迭代，配合开发团队完成测试和上线；
5. 负责运维文档的编写和维护，建立完善的运维管理体系。

【任职要求】
1. 本科及以上学历，计算机科学与技术、网络工程、信息安全等相关专业；
2. 熟悉 Linux 操作系统，具备基本的命令行操作和脚本编写能力；
3. 了解 MySQL 数据库的基本操作和维护，具备基本的 SQL 能力；
4. 熟悉网络基础知识和常见网络设备配置；
5. 具备良好的故障排查能力和应急响应能力，能够承受一定的工作压力。

【福利待遇】
1. 省级事业单位编制，工作稳定有保障；
2. 五险一金、带薪年假、节日福利；
3. 完善的培训体系，提供技术认证支持。""",
        "requirements": [
            "本科及以上学历，计算机科学与技术、网络工程、信息安全等相关专业",
            "熟悉 Linux 操作系统，具备基本的命令行操作和脚本编写能力",
            "了解 MySQL 数据库的基本操作和维护",
            "熟悉网络基础知识和常见网络设备配置",
            "具备良好的故障排查能力和应急响应能力"
        ],
        "preferred_skills": ["Linux", "MySQL", "网络运维", "Shell", "监控"],
        "tags": ["政府", "运维", "广州", "稳定", "省级"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=8),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_005",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_005",
        "company_website": "https://gdjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_006",
        "company": "惠州市公共就业和人才服务中心",
        "company_type": "government",
        "title": "招聘专员（校招）",
        "location": "惠州",
        "locations": ["惠州"],
        "job_type": "full_time",
        "salary_range": {"min": 6, "max": 10, "unit": "K/月"},
        "description": """【岗位职责】
1. 负责组织和管理线上线下招聘会活动，包括场地布置、嘉宾接待、现场协调等；
2. 对接用人单位，了解招聘需求，协助企业发布招聘信息；
3. 开展求职者服务，提供岗位推荐、政策咨询等一站式就业服务；
4. 参与招聘活动的宣传推广，扩大活动影响力和覆盖面；
5. 完成招聘数据的统计分析和活动总结报告。

【任职要求】
1. 2025 届本科及以上学历，市场营销、人力资源管理、公共管理等相关专业优先；
2. 具备良好的沟通协调能力，能够胜任与用人单位和求职者的对接工作；
3. 具备基本的活动策划和执行能力，有活动组织经验者优先；
4. 熟练使用 Office 办公软件，具备基本的文档处理能力；
5. 性格开朗，责任心强，能够适应招聘会期间的加班和出差。

【福利待遇】
1. 政府事业单位编制，工作环境稳定；
2. 五险一金、带薪年假、节日福利；
3. 位于惠州市中心，交通便利，生活成本相对较低。""",
        "requirements": [
            "2025 届本科及以上学历，市场营销、人力资源管理、公共管理等相关专业优先",
            "具备良好的沟通协调能力，能够胜任与用人单位和求职者的对接工作",
            "具备基本的活动策划和执行能力，有活动组织经验者优先",
            "熟练使用 Office 办公软件，具备基本的文档处理能力",
            "性格开朗，责任心强，能够适应招聘会期间的加班和出差"
        ],
        "preferred_skills": ["招聘", "沟通", "活动策划", "Office", "执行"],
        "tags": ["政府", "校招", "惠州", "招聘", "事业单位"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=3),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_006",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_006",
        "company_website": "https://hzrss.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
]


class GuangdongRCSource(JobSourceAdapter):
    """广东人才网适配器 — 广东省人力资源和社会保障厅主办"""

    @property
    def source_name(self) -> str:
        return "gdrc"

    @property
    def source_type(self) -> str:
        return "gdrc"

    @property
    def base_url(self) -> str:
        return "https://www.gdrc.com"

    async def fetch_jobs(
        self, keyword: str = "", location: str = "", limit: int = 20
    ) -> List[Dict[str, Any]]:
        logger.info(f"[广东人才网] 采集岗位: keyword={keyword}, location={location}")
        jobs = []
        for raw in _GDRC_JOBS:
            if keyword:
                kw = keyword.lower()
                match = (
                    kw in raw["title"].lower()
                    or kw in raw["company"].lower()
                    or kw in raw["description"].lower()
                )
                if not match:
                    continue
            if location and location not in raw["location"]:
                continue
            jobs.append(self.normalize_job(raw))
            if len(jobs) >= limit:
                break
        logger.info(f"[广东人才网] 返回 {len(jobs)} 条岗位")
        return jobs

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[广东人才网] 获取详情: job_id={job_id}")
        for raw in _GDRC_JOBS:
            if raw["source_job_id"] == job_id:
                return self.normalize_job(raw)
        return None


class GuangdongPublicSource(JobSourceAdapter):
    """广东公共招聘平台适配器 — 省级公共就业服务平台"""

    @property
    def source_name(self) -> str:
        return "gd_public"

    @property
    def source_type(self) -> str:
        return "gd_public"

    @property
    def base_url(self) -> str:
        return "https://gdreclruit.gov.cn"

    async def fetch_jobs(
        self, keyword: str = "", location: str = "", limit: int = 20
    ) -> List[Dict[str, Any]]:
        logger.info(f"[广东公共招聘] 采集岗位: keyword={keyword}, location={location}")
        jobs = []
        for raw in _GDPUBLIC_JOBS:
            if keyword:
                kw = keyword.lower()
                match = (
                    kw in raw["title"].lower()
                    or kw in raw["company"].lower()
                    or kw in raw["description"].lower()
                )
                if not match:
                    continue
            if location and location not in raw["location"]:
                continue
            jobs.append(self.normalize_job(raw))
            if len(jobs) >= limit:
                break
        logger.info(f"[广东公共招聘] 返回 {len(jobs)} 条岗位")
        return jobs

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[广东公共招聘] 获取详情: job_id={job_id}")
        for raw in _GDPUBLIC_JOBS:
            if raw["source_job_id"] == job_id:
                return self.normalize_job(raw)
        return None


# 注册到全局适配器表
ADAPTER_REGISTRY["gdrc"] = GuangdongRCSource()
ADAPTER_REGISTRY["gd_public"] = GuangdongPublicSource()
