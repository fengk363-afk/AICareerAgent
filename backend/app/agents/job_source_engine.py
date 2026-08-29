"""
JobSourceEngine — 统一岗位数据源系统
支持多种招聘平台，MVP 使用 Mock 数据
"""
import re
import html as html_module
import unicodedata
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
from sqlalchemy import select, func
from app.db.database import get_db
from app.schemas.models import JobResponse
from app.agents.job_source_adapters import ADAPTER_REGISTRY, get_adapter


# ── V7.1 岗位标准化函数 ──────────────────────────────────────────

# 公司后缀模式（按长度降序排列，避免部分匹配）
_COMPANY_SUFFIX_PATTERNS = [
    r'\s*,?\s*Inc\.?$',
    r'\s*,?\s*Ltd\.?$',
    r'\s*,?\s*Limited$',
    r'\s*,?\s*LLC$',
    r'\s*,?\s*Corp\.?$',
    r'\s*,?\s*Corporation$',
    r'\s*,?\s*Co\.?$',
    r'\s*,?\s*GmbH$',
    r'\s*,?\s*AG$',
    r'\s*,?\s*BV$',
    r'\s*,?\s*NV$',
    r'\s*,?\s*SA$',
    r'\s*,?\s*AB$',
    r'\s*,?\s*Pty\.?$',
    r'\s*,?\s*Group$',
    r'\s*,?\s*Holdings?$',
    r'\s*,?\s*International$',
    r'\s*,?\s*International\s+Group$',
    r'\s*,?\s*China$',
    r'\s*,?\s*中国$',
    r'\s*,?\s*有限公司$',
    r'\s*,?\s*股份有限公司$',
    r'\s*,?\s*集团$',
]

# 职位级别前缀（保留，不删除）
_LEVEL_PREFIXES = [
    r'^(Junior\s+|Entry\s+Level\s+|Entry\s+Level\s+)?',
    r'^(Senior\s+|Lead\s+|Staff\s+|Principal\s+|Distinguished\s+|Fellow\s+)?',
    r'^(Associate\s+|Mid\s+Level\s+|Mid\s+Level\s+)?',
]

# 中国城市别名映射
_CITY_ALIASES = {
    '北京': 'beijing', '北京市': 'beijing',
    '上海': 'shanghai', '上海市': 'shanghai',
    '广州': 'guangzhou', '广州市': 'guangzhou',
    '深圳': 'shenzhen', '深圳市': 'shenzhen',
    '杭州': 'hangzhou', '杭州市': 'hangzhou',
    '成都': 'chengdu', '成都市': 'chengdu',
    '武汉': 'wuhan', '武汉市': 'wuhan',
    '南京': 'nanjing', '南京市': 'nanjing',
    '重庆': 'chongqing', '重庆市': 'chongqing',
    '西安': 'xian', '西安市': 'xian',
    '苏州': 'suzhou', '苏州市': 'suzhou',
    '天津': 'tianjin', '天津市': 'tianjin',
    '长沙': 'changsha', '长沙市': 'changsha',
    '宁波': 'ningbo', '宁波市': 'ningbo',
    '青岛': 'qingdao', '青岛市': 'qingdao',
    '大连': 'dalian', '大连市': 'dalian',
    '厦门': 'xiamen', '厦门市': 'xiamen',
    '福州': 'fuzhou', '福州市': 'fuzhou',
    '合肥': 'hefei', '合肥市': 'hefei',
    '郑州': 'zhengzhou', '郑州市': 'zhengzhou',
    '沈阳': 'shenyang', '沈阳市': 'shenyang',
    '哈尔滨': 'harbin', '哈尔滨市': 'harbin',
    '长春': 'changchun', '长春市': 'changchun',
    '济南': 'jinan', '济南市': 'jinan',
    '昆明': 'kunming', '昆明市': 'kunming',
    '贵阳': 'guiyang', '贵阳市': 'guiyang',
    '南昌': 'nanchang', '南昌市': 'nanchang',
    '太原': 'taiyuan', '太原市': 'taiyuan',
    '石家庄': 'shijiazhuang', '石家庄市': 'shijiazhuang',
    '南宁': 'nanning', '南宁市': 'nanning',
    '海口': 'haikou', '海口市': 'haikou',
    '兰州': 'lanzhou', '兰州市': 'lanzhou',
    '乌鲁木齐': 'urumqi', '乌鲁木齐市': 'urumqi',
    '呼和浩特': 'hohhot', '呼和浩特市': 'hohhot',
    '银川': 'yinchuan', '银川市': 'yinchuan',
    '西宁': 'xining', '西宁市': 'xining',
    '拉萨': 'lhasa', '拉萨市': 'lhasa',
    '珠海': 'zhuhai', '珠海市': 'zhuhai',
    '佛山': 'foshan', '佛山市': 'foshan',
    '东莞': 'dongguan', '东莞市': 'dongguan',
    '无锡': 'wuxi', '无锡市': 'wuxi',
    '常州': 'changzhou', '常州市': 'changzhou',
    '徐州': 'xuzhou', '徐州市': 'xuzhou',
    '南通': 'nantong', '南通市': 'nantong',
    '扬州': 'yangzhou', '扬州市': 'yangzhou',
    '盐城': 'yancheng', '盐城市': 'yancheng',
    '镇江': 'zhenjiang', '镇江市': 'zhenjiang',
    '泰州': 'taizhou', '泰州市': 'taizhou',
    '淮安': 'huai_an', '淮安市': "huai_an",
    '宿迁': 'suqian', '宿迁市': 'suqian',
    '连云港': 'lianyungang', '连云港市': 'lianyungang',
    '蚌埠': 'bengbu', '蚌埠市': 'bengbu',
    '芜湖': 'wuhu', '芜湖市': 'wuhu',
    '淮南': 'huainan', '淮南市': 'huainan',
    '马鞍山': 'ma_anshan', '马鞍山市': "ma_anshan",
    '淮北': 'huaibei', '淮北市': 'huaibei',
    '铜陵': 'tongling', '铜陵市': 'tongling',
    '安庆': 'anqing', '安庆市': 'anqing',
    '黄山': 'huangshan', '黄山市': 'huangshan',
    '滁州': 'chuzhou', '滁州市': 'chuzhou',
    '阜阳': 'fuyang', '阜阳市': 'fuyang',
    '宿州': 'suzhou_cn', '宿州市': 'suzhou_cn',
    '六安': 'lu_an', '六安市': "lu_an",
    '亳州': 'bozhou', '亳州市': 'bozhou',
    '池州': 'chizhou', '池州市': 'chizhou',
    '宣城': 'xuancheng', '宣城市': 'xuancheng',
    '福州': 'fuzhou', '福州市': 'fuzhou',
    '厦门': 'xiamen', '厦门市': 'xiamen',
    '莆田': 'putian', '莆田市': 'putian',
    '三明': 'sanming', '三明市': 'sanming',
    '泉州': 'quanzhou', '泉州市': 'quanzhou',
    '漳州': 'zhangzhou', '漳州市': 'zhangzhou',
    '南平': 'nanping', '南平市': 'nanping',
    '龙岩': 'longyan', '龙岩市': 'longyan',
    '宁德': 'ningde', '宁德市': 'ningde',
    '福州': 'fuzhou', '福州市': 'fuzhou',
    '福州': 'fuzhou', '福州市': 'fuzhou',
}

# 美国城市别名
_US_CITY_ALIASES = {
    'sf': 'san francisco', 'san francisco, ca': 'san francisco',
    'new york, ny': 'new york', 'nyc': 'new york',
    'los angeles, ca': 'los angeles', 'la': 'los angeles',
    'chicago, il': 'chicago',
    'houston, tx': 'houston',
    'phoenix, az': 'phoenix',
    'dallas, tx': 'dallas',
    'austin, tx': 'austin',
    'seattle, wa': 'seattle',
    'denver, co': 'denver',
    'boston, ma': 'boston',
    'portland, or': 'portland',
    'atlanta, ga': 'atlanta',
    'miami, fl': 'miami',
    'san diego, ca': 'san diego',
    'washington, dc': 'washington dc',
    'palo alto, ca': 'palo alto',
    'mountain view, ca': 'mountain view',
    'cupertino, ca': 'cupertino',
    'sunnyvale, ca': 'sunnyvale',
    'redmond, wa': 'redmond',
    'bellevue, wa': 'bellevue',
    'san jose, ca': 'san jose',
    ' Fremont, ca': 'fremont',
    'irvine, ca': 'irvine',
    'sandiego': 'san diego',
    'la, ca': 'los angeles',
}


def normalize_company(raw: str) -> str:
    """
    归一化公司名称：
    - 去 HTML 标签
    - Unicode 标准化（NFKC）
    - 去前后空格
    - 去常见公司后缀（Inc., LLC, Ltd. 等）
    - 转小写
    - 多空格合一
    """
    if not raw:
        return ""
    # 去 HTML
    text = re.sub(r'<[^>]+>', '', raw)
    text = html_module.unescape(text)
    # Unicode 标准化
    text = unicodedata.normalize('NFKC', text)
    # 去前后空格
    text = text.strip()
    # 去公司后缀（按长度降序，避免部分匹配）
    for pattern in _COMPANY_SUFFIX_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # 去前后空格
    text = text.strip()
    # 去逗号
    text = text.replace(',', '').strip()
    # 多空格合一
    text = re.sub(r'\s+', ' ', text)
    # 转小写
    text = text.lower()
    return text


def normalize_title(raw: str) -> str:
    """
    归一化职位名称：
    - 去 HTML 标签
    - Unicode 标准化
    - 去括号内容（如（校招）、(校招)）
    - 多空格合一
    - 转小写
    - 保留职位级别信息（Senior、Junior 等）
    """
    if not raw:
        return ""
    # 去 HTML
    text = re.sub(r'<[^>]+>', '', raw)
    text = html_module.unescape(text)
    # Unicode 标准化
    text = unicodedata.normalize('NFKC', text)
    # 去括号内容（中英文括号）
    text = re.sub(r'[（(].*?[）)]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # 转小写
    text = text.lower()
    return text


def normalize_location(raw: str) -> str:
    """
    归一化地点：
    - 去 HTML 标签
    - Unicode 标准化
    - 多空格合一
    - 转小写
    - 统一标点（逗号+空格）
    - 中国城市别名映射
    - 美国城市别名映射
    - Remote 统一
    """
    if not raw:
        return ""
    # 去 HTML
    text = re.sub(r'<[^>]+>', '', raw)
    text = html_module.unescape(text)
    # Unicode 标准化
    text = unicodedata.normalize('NFKC', text)
    # 多空格合一
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # Remote 统一
    remote_patterns = ['remote', '远程', 'work from home', 'wfh', 'home office']
    for rp in remote_patterns:
        if rp.lower() in text.lower():
            return 'remote'
    # 转小写
    text = text.lower()
    # 统一标点：逗号前后空格
    text = re.sub(r'\s*,\s*', ', ', text)
    # 中国城市别名（按长度降序，避免部分匹配）
    for cn_full, cn_norm in sorted(_CITY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if cn_full in text:
            text = text.replace(cn_full, cn_norm)
    # 美国城市别名（按长度降序）
    for us_alias, us_norm in sorted(_US_CITY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if us_alias in text:
            text = text.replace(us_alias, us_norm)
    return text.strip()


async def find_possible_duplicates(db, job: Job, limit: int = 10) -> List[Dict[str, Any]]:
    """
    查找可能的重复岗位（候选检测，不自动合并）。
    使用 normalized_* 字段 + 索引缩小候选集合，再对候选做 rapidfuzz 比较。
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        logger.warning("[V7.1] rapidfuzz 未安装，跳过相似度计算")
        return []

    if not job.normalized_company or not job.normalized_title:
        return []

    # 职位级别前缀（用于排除不同级别的岗位）
    LEVEL_PREFIXES = ['junior', 'senior', 'lead', 'staff', 'principal', 'distinguished', 'fellow', 'associate', 'mid']

    def has_level_prefix(title: str) -> bool:
        """检查标题是否包含级别前缀"""
        for prefix in LEVEL_PREFIXES:
            if title.startswith(prefix + ' '):
                return True
        return False

    # 先用数据库字段缩小候选集合
    query = select(Job).where(
        Job.normalized_company == job.normalized_company,
        Job.id != job.id,
        Job.status == 'active'
    ).limit(limit * 3)  # 多取一些候选

    result = await db.execute(query)
    candidates = result.scalars().all()

    if not candidates:
        return []

    # 对候选做 title 相似度过滤
    similar = []
    job_title_norm = job.normalized_title
    job_loc_norm = job.normalized_location or ""
    job_has_level = has_level_prefix(job_title_norm)

    for candidate in candidates:
        cand_title_norm = candidate.normalized_title or ""
        cand_has_level = has_level_prefix(cand_title_norm)

        # 级别前缀检查：如果一个有级别前缀另一个没有，降低相似度阈值
        # 例如：Software Engineer vs Senior Software Engineer 不应视为重复
        title_sim = fuzz.WRatio(job_title_norm, cand_title_norm)

        # 如果级别不同，要求更高的相似度才能视为候选
        if job_has_level != cand_has_level:
            # 不同级别：需要 >= 95 才视为候选（避免误判）
            if title_sim < 95:
                continue
            confidence = 'low'  # 不同级别，低置信度
        else:
            # 相同级别或都无级别：>= 90 高置信度，>= 80 中置信度
            if title_sim < 80:
                continue
            confidence = 'high' if title_sim >= 90 else 'medium'

        # location 兼容性检查
        cand_loc = candidate.normalized_location or ""
        loc_match = True
        if job_loc_norm and cand_loc:
            # 如果都是 remote，匹配
            if job_loc_norm == 'remote' and cand_loc == 'remote':
                loc_match = True
            # 如果候选地点包含在 job 地点中，或反之
            elif job_loc_norm in cand_loc or cand_loc in job_loc_norm:
                loc_match = True
            # 如果都包含相同城市名
            elif job_loc_norm and cand_loc:
                job_cities = set(job_loc_norm.split(','))
                cand_cities = set(cand_loc.split(','))
                if job_cities & cand_cities:
                    loc_match = True
            else:
                loc_match = False

        if not loc_match:
            continue

        similar.append({
            'job_id': candidate.id,
            'source': candidate.source,
            'source_job_id': candidate.source_job_id,
            'company': candidate.company,
            'title': candidate.title,
            'normalized_title': candidate.normalized_title,
            'location': candidate.location,
            'normalized_location': candidate.normalized_location,
            'title_similarity': title_sim,
            'confidence': 'high' if title_sim >= 90 else 'medium',
        })

    # 按相似度排序
    similar.sort(key=lambda x: x['title_similarity'], reverse=True)
    return similar[:limit]


async def _find_possible_duplicates_async(db, job, limit=10):
    """异步包装，供同步代码调用"""
    return find_possible_duplicates(db, job, limit)


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
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """搜索岗位（支持多维度筛选），返回分页结果 {jobs, total, limit, offset, has_more}"""
        async for db in get_db():
            # 构建基础查询条件（jobs 和 count 共用）
            def _build_query():
                q = select(Job)
                # 默认只展示 ACTIVE 岗位
                if status is None:
                    q = q.where(Job.status == "active")
                else:
                    q = q.where(Job.status == status)

                if keyword:
                    kw = keyword.lower()
                    q = q.where(
                        (Job.title.ilike(f"%{kw}%")) |
                        (Job.company.ilike(f"%{kw}%")) |
                        (Job.description.ilike(f"%{kw}%"))
                    )
                if location:
                    q = q.where(Job.location.ilike(f"%{location}%"))
                if locations:
                    loc_list = [l.strip() for l in locations.split(",") if l.strip()]
                    if loc_list:
                        from sqlalchemy import or_
                        location_conditions = [Job.locations.contains([loc]) for loc in loc_list]
                        q = q.where(or_(*location_conditions))
                if job_type:
                    q = q.where(Job.job_type == job_type)
                if company_type:
                    q = q.where(Job.company_type == company_type)
                if is_foreign is not None:
                    q = q.where(Job.is_foreign == is_foreign)
                if is_remote is not None:
                    q = q.where(Job.is_remote == is_remote)
                if has_apply_url is not None:
                    if has_apply_url:
                        q = q.where(Job.apply_url.isnot(None))
                    else:
                        q = q.where(Job.apply_url.is_(None))
                if salary_min is not None:
                    q = q.where(Job.salary_range["min"].as_integer() >= salary_min)
                if salary_max is not None:
                    q = q.where(Job.salary_range["max"].as_integer() <= salary_max)
                if salary_ranges:
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
                            q = q.where(or_(*salary_conditions))
                if tags:
                    for tag in tags:
                        q = q.where(Job.tags.contains([tag]))
                if source_type:
                    q = q.where(Job.source_type == source_type)
                if company_country:
                    q = q.where(Job.company_country.ilike(f"%{company_country}%"))
                if visa_support is not None:
                    q = q.where(Job.visa_support == visa_support)
                if english_required is not None:
                    q = q.where(Job.english_required == english_required)
                if graduate_program is not None:
                    q = q.where(Job.graduate_program == graduate_program)
                if campus_recruitment is not None:
                    q = q.where(Job.campus_recruitment == campus_recruitment)
                if season:
                    q = q.where(Job.season == season)
                if industry:
                    industry_list = [i.strip() for i in industry.split(",") if i.strip()]
                    if industry_list:
                        from sqlalchemy import or_
                        industry_conditions = [Job.industry == ind for ind in industry_list]
                        q = q.where(or_(*industry_conditions))
                if job_category:
                    category_list = [c.strip() for c in job_category.split(",") if c.strip()]
                    if category_list:
                        from sqlalchemy import or_
                        category_conditions = [Job.job_category == cat for cat in category_list]
                        q = q.where(or_(*category_conditions))
                return q

            # 先查 total
            count_query = select(func.count()).select_from(_build_query())
            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            # 再查分页数据
            data_query = _build_query().offset(offset).limit(limit)
            result = await db.execute(data_query)
            jobs = [JobResponse.model_validate(r) for r in result.scalars().all()]

            has_more = (offset + len(jobs)) < total
            return {
                "jobs": jobs,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
            }

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
