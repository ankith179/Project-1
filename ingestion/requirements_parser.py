import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ParsedRequirement:
    req_identifier: str
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: str = "MEDIUM"
    category: str = "FUNCTIONAL"
    source_file: str = ""
    line_start: int = 1
    line_end: int = 1
    version: str = "1.0"
    raw_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RequirementsParser:
    """
    Robust parser for software requirements in Markdown, Plain Text, and User Story formats.
    Extracts structured requirement entities with IDs, titles, descriptions,
    acceptance criteria, priorities, and line bounds.
    """

    # Patterns to detect requirement headers or identifiers
    REQ_HEADER_PATTERN = re.compile(
        r'^(?:#{1,6}\s+)?(?:\[)?(REQ(?:UIREMENT)?[-_ ]?\d+|US[-_ ]?\d+|FEATURE[-_ ]?\d+|F[-_ ]?\d+)(?:\])?[:\s\-\–]*(.*)$',
        re.IGNORECASE | re.MULTILINE
    )

    PRIORITY_PATTERN = re.compile(r'\b(?:Priority|Severity):\s*([a-zA-Z]+)', re.IGNORECASE)
    CATEGORY_PATTERN = re.compile(r'\b(?:Category|Type):\s*([a-zA-Z0-9_\- ]+)', re.IGNORECASE)
    VERSION_PATTERN = re.compile(r'\b(?:Version|Release):\s*([vV]?\d+(?:\.\d+)*)', re.IGNORECASE)

    def parse_file(self, file_path: str) -> List[ParsedRequirement]:
        """Parses a requirements file (Markdown or TXT) and returns a list of ParsedRequirement."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Requirements file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        return self.parse_content("".join(lines), source_file=file_path)

    def parse_content(self, content: str, source_file: str = "inline") -> List[ParsedRequirement]:
        """Parses text content containing one or more requirements."""
        lines = content.splitlines(keepends=True)
        if not lines:
            return []

        # Find all section headers that match requirement identifier patterns
        matches = []
        for idx, line in enumerate(lines, start=1):
            m = self.REQ_HEADER_PATTERN.match(line.strip())
            if m:
                req_id = m.group(1).upper().replace(" ", "-").replace("_", "-")
                if not re.search(r'[-_]', req_id):
                    # Standardize format e.g. REQ1 -> REQ-1
                    req_id = re.sub(r'([A-Za-z]+)(\d+)', r'\1-\2', req_id)
                title = m.group(2).strip() or req_id
                matches.append((idx, req_id, title))

        # If no explicit REQ headers found, check if the file itself is a single requirement/user story
        if not matches:
            first_non_empty = next((l.strip() for l in lines if l.strip()), "Untitled Requirement")
            title = first_non_empty.lstrip('#*-> \t').strip() or "Untitled Requirement"
            req_id = "REQ-001"
            return [self._extract_requirement_details(
                req_id=req_id,
                title=title,
                lines=lines,
                line_start=1,
                line_end=len(lines),
                source_file=source_file
            )]

        results = []
        for i in range(len(matches)):
            start_line, req_id, title = matches[i]
            end_line = matches[i + 1][0] - 1 if i + 1 < len(matches) else len(lines)

            req_lines = lines[start_line - 1:end_line]
            req = self._extract_requirement_details(
                req_id=req_id,
                title=title,
                lines=req_lines,
                line_start=start_line,
                line_end=end_line,
                source_file=source_file
            )
            results.append(req)

        return results

    def _extract_requirement_details(
        self,
        req_id: str,
        title: str,
        lines: List[str],
        line_start: int,
        line_end: int,
        source_file: str
    ) -> ParsedRequirement:
        text = "".join(lines)

        priority = "MEDIUM"
        m_pri = self.PRIORITY_PATTERN.search(text)
        if m_pri:
            priority = m_pri.group(1).upper()

        category = "FUNCTIONAL"
        m_cat = self.CATEGORY_PATTERN.search(text)
        if m_cat:
            category = m_cat.group(1).strip().upper()

        version = "1.0"
        m_ver = self.VERSION_PATTERN.search(text)
        if m_ver:
            version = m_ver.group(1).strip()

        # Extract acceptance criteria and description
        acceptance_criteria = []
        desc_lines = []
        in_ac_section = False

        for line in lines[1:]:  # Skip the header line
            stripped = line.strip()
            clean_head = stripped.lstrip('#*- \t').lower()

            if clean_head.startswith("acceptance criteria") or clean_head.startswith("conditions of satisfaction") or clean_head.startswith("scenarios:"):
                in_ac_section = True
                continue
            elif in_ac_section and (stripped.startswith("#") or (stripped and not stripped.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "Given", "When", "Then")))):
                # If we encounter another section header or distinct text, exit AC section
                if stripped.startswith("#"):
                    in_ac_section = False

            if in_ac_section:
                # Bullet or Given-When-Then item
                cleaned = re.sub(r'^[\*\-\d\.]+\s*', '', stripped)
                if cleaned:
                    acceptance_criteria.append(cleaned)
            else:
                # Part of general description
                # Filter out metadata lines like Priority: High from main description text
                if not self.PRIORITY_PATTERN.search(stripped) and \
                   not self.CATEGORY_PATTERN.search(stripped) and \
                   not self.VERSION_PATTERN.search(stripped):
                    desc_lines.append(line)

        description = "".join(desc_lines).strip()
        if not description:
            description = title

        metadata = {
            "num_lines": line_end - line_start + 1,
            "has_acceptance_criteria": len(acceptance_criteria) > 0,
            "ac_count": len(acceptance_criteria),
        }

        return ParsedRequirement(
            req_identifier=req_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            category=category,
            source_file=source_file,
            line_start=line_start,
            line_end=line_end,
            version=version,
            raw_content=text,
            metadata=metadata
        )
