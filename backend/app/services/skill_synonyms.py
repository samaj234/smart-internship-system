"""
Skill synonym/alias mapping for the Smart Internship System.

Purpose: normalizes skill names so that equivalent terms
map to the same canonical skill, preventing false "missing skill"
reports when employers and students use different terminology
for the same skill.

Structure: each key is a canonical skill name, and its value
is a list of aliases that should be treated as equivalent.
The normalize_skill() function maps any alias back to its
canonical form before comparison.
"""

SKILL_SYNONYMS = {
    # Programming languages
    "javascript": ["js", "java script", "ecmascript", "es6", "es2015", "vanilla js"],
    "typescript": ["ts"],
    "python": ["python3", "python2", "py"],
    "java": ["java se", "java ee", "core java"],
    "c++": ["cpp", "c plus plus", "cplusplus"],
    "c#": ["csharp", "c sharp", "dotnet c#"],
    "php": ["php7", "php8"],
    "kotlin": ["kotlin android"],
    "swift": ["swift ios", "swiftui"],
    "golang": ["go", "go lang"],
    "rust": ["rust lang"],
    "scala": ["scala lang"],

    # Web frameworks & libraries
    "react": ["reactjs", "react.js", "react js", "react native"],
    "angular": ["angularjs", "angular.js", "angular js"],
    "vue": ["vuejs", "vue.js", "vue js"],
    "node.js": ["nodejs", "node js", "node"],
    "django": ["django rest framework", "drf"],
    "flask": ["flask python", "flask api"],
    "fastapi": ["fast api"],
    "spring": ["spring boot", "spring framework", "springboot"],
    "express": ["expressjs", "express.js"],
    "next.js": ["nextjs", "next js"],
    "nuxt": ["nuxtjs", "nuxt.js"],

    # Databases
    "sql": ["structured query language", "t-sql", "pl/sql", "mysql", "sql server"],
    "postgresql": ["postgres", "psql", "pg"],
    "mongodb": ["mongo", "mongo db"],
    "mysql": ["my sql"],
    "sqlite": ["sqlite3"],
    "redis": ["redis cache"],
    "elasticsearch": ["elastic search", "elastic"],
    "oracle": ["oracle db", "oracle database"],
    "microsoft sql server": ["mssql", "ms sql", "sql server"],

    # Cloud & DevOps
    "aws": ["amazon web services", "amazon aws"],
    "azure": ["microsoft azure", "ms azure"],
    "google cloud": ["gcp", "google cloud platform", "google cloud services"],
    "docker": ["docker container", "containerization"],
    "kubernetes": ["k8s", "kube"],
    "terraform": ["terraform iac"],
    "jenkins": ["jenkins ci"],
    "github actions": ["gh actions"],
    "ci/cd": ["continuous integration", "continuous deployment", "cicd"],

    # Data science & ML
    "machine learning": ["ml", "machine-learning"],
    "deep learning": ["dl", "deep-learning", "neural networks"],
    "natural language processing": ["nlp", "natural-language-processing"],
    "computer vision": ["cv", "image recognition"],
    "artificial intelligence": ["ai"],
    "data science": ["data analytics", "data analysis"],
    "tensorflow": ["tf", "tensor flow"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "pandas": ["pandas python"],
    "numpy": ["np", "numpy python"],
    "matplotlib": ["pyplot", "matplotlib python"],
    "tableau": ["tableau desktop", "tableau server"],
    "power bi": ["powerbi", "microsoft power bi", "ms power bi"],

    # Version control
    "git": ["github", "gitlab", "bitbucket", "version control"],
    "github": ["gh", "git hub"],
    "gitlab": ["git lab"],

    # Mobile
    "android": ["android development", "android studio"],
    "ios": ["ios development", "xcode"],
    "react native": ["rn", "react-native"],
    "flutter": ["flutter dart", "dart flutter"],

    # Project management
    "project management": ["pm", "project manager"],
    "agile": ["agile methodology", "agile development"],
    "scrum": ["scrum methodology", "scrum master"],
    "jira": ["atlassian jira"],
    "trello": ["trello board"],

    # Design
    "ui/ux": ["ui", "ux", "user interface", "user experience", "ui design", "ux design"],
    "figma": ["figma design"],
    "photoshop": ["adobe photoshop", "ps"],
    "illustrator": ["adobe illustrator", "ai"],
    "sketch": ["sketch app"],

    # Microsoft Office
    "excel": ["microsoft excel", "ms excel", "spreadsheets"],
    "word": ["microsoft word", "ms word"],
    "powerpoint": ["microsoft powerpoint", "ms powerpoint", "ppt"],
    "microsoft office": ["ms office", "office 365", "microsoft 365"],
    "microsoft word": ["word", "ms word", "microsoft word processor"],
    "microsoft excel": ["excel", "ms excel", "spreadsheets", "spreadsheet"],
    "data entry": ["data-entry", "data input", "data processing", "typing"],
    "microsoft office": ["ms office", "office 365", "microsoft 365", "office suite"],
        
    # Other technical
    "rest api": ["rest", "restful", "restful api", "api", "rest apis"],
    "graphql": ["graph ql"],
    "html": ["html5", "hypertext markup language"],
    "css": ["css3", "cascading style sheets"],
    "linux": ["unix", "ubuntu", "centos", "bash", "shell scripting"],
    "networking": ["computer networking", "network administration"],
    "cybersecurity": ["cyber security", "information security", "infosec"],
    "blockchain": ["blockchain technology", "web3"],
    "erp": ["enterprise resource planning", "sap", "oracle erp"],
    "salesforce": ["sfdc", "salesforce crm"],
    "report writing": ["report-writing", "writing reports", "business writing"],
    "customer service": ["customer support", "client service", "customer care"],
    "communication": ["communications", "verbal communication", "written communication"],
    "teamwork": ["team work", "team player", "collaborative", "collaboration"],
    # Soft skills
    "communication": ["verbal communication", "written communication", "communication skills"],
    "leadership": ["team leadership", "people management", "managing teams"],
    "problem solving": ["problem-solving", "analytical skills", "critical thinking"],
    "teamwork": ["team player", "collaboration", "collaborative"],
    "time management": ["multitasking", "prioritization"],
    "presentation": ["public speaking", "presenting"],
    "financial reporting": ["financial reports", "financial statements", "reporting"],
    "financial analysis": ["financial analytics", "finance analysis"],
    "banking operations": ["banking", "bank operations", "banking services"],
}

# Build reverse lookup: alias → canonical name
# This lets us quickly find the canonical form of any alias
_ALIAS_TO_CANONICAL = {}
for canonical, aliases in SKILL_SYNONYMS.items():
    _ALIAS_TO_CANONICAL[canonical] = canonical  # canonical maps to itself
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower().strip()] = canonical


def normalize_skill(skill: str) -> str:
    """
    Maps a skill string to its canonical form.

    Examples:
    normalize_skill("JS") → "javascript"
    normalize_skill("ML") → "machine learning"
    normalize_skill("ReactJS") → "react"
    normalize_skill("PostgreSQL") → "postgresql"

    If no synonym is found, returns the lowercased/stripped
    original — so unknown skills still compare correctly
    with each other.
    """
    normalized = skill.lower().strip()
    return _ALIAS_TO_CANONICAL.get(normalized, normalized)


def skills_match(skill_a: str, skill_b: str) -> bool:
    """
    Returns True if two skill strings refer to the same skill,
    accounting for synonyms, aliases, and partial matches.

    Matching strategy (in order):
    1. Exact canonical match — normalize both and compare
    2. Partial match — one normalized form contains the other
       (handles "Python programming" vs "Python")
    """
    canon_a = normalize_skill(skill_a)
    canon_b = normalize_skill(skill_b)

    # Exact canonical match
    if canon_a == canon_b:
        return True

    # Partial match
    if canon_a in canon_b or canon_b in canon_a:
        return True

    return False