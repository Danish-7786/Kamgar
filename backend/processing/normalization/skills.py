"""Skill normalization: messy spelling -> canonical spelling.

The map is DATA. Adding "Golang -> Go" is a one-line edit here, never a
change to logic. Keys are lowercased; values are the canonical form we keep.
Unknown skills fall through unchanged (stripped) — we never drop a skill just
because it isn't in the map.
"""

from __future__ import annotations

SKILL_ALIASES: dict[str, str] = {
    "nodejs": "Node.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "react native": "React Native",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "golang": "Go",
    "go": "Go",
    "py": "Python",
    "python": "Python",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "gcp": "Google Cloud",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "cpp": "C++",
    "c++": "C++",
    "csharp": "C#",
    "c#": "C#",
    "restful": "REST",
    "rest": "REST",
    "graphql": "GraphQL",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
}


def normalize_skill(skill: str) -> str:
    key = skill.strip().lower()
    return SKILL_ALIASES.get(key, skill.strip())


def normalize_skills(skills: list[str]) -> list[str]:
    """Canonicalize then de-dupe — crucial because aliasing collapses
    variants (["NodeJS", "Node.js"] -> ["Node.js"])."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in skills:
        canonical = normalize_skill(raw)
        if not canonical:
            continue
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(canonical)
    return out
