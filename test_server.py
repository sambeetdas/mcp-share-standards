"""Quick test to verify the MCP Standards Server loads and works correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from standards_server.stores.rules_store import RulesStore
from standards_server.stores.skills_store import SkillsStore
from standards_server.stores.audit_store import AuditStore
from standards_server.models import Language, RuleCategory, Severity, ViolationReport


def test_stores():
    """Test that rules and skills load correctly."""
    print("=" * 60)
    print("MCP Standards Server — Test Suite")
    print("=" * 60)

    # Test Rules Store
    print("\n--- Rules Store ---")
    rs = RulesStore(Path("standards"))
    rs.load()
    rules = rs.list_all()
    print(f"Total rules loaded: {len(rules)}")
    for r in rules:
        print(f"  [{r.language.value}] {r.id} ({r.category.value}) - {r.description[:60]}...")

    # Test query
    csharp_rules = rs.query(language=Language.CSHARP)
    print(f"\nC# rules: {len(csharp_rules)}")
    naming_rules = rs.query(language=Language.CSHARP, category=RuleCategory.NAMING)
    print(f"C# naming rules: {len(naming_rules)}")

    # Test get by ID
    rule = rs.get("csharp/naming-conventions")
    assert rule is not None, "Should find csharp/naming-conventions"
    print(f"\nGet by ID test: '{rule.name}' - PASS")
    assert len(rule.content) > 100, "Rule content should be substantial"
    print(f"Content length: {len(rule.content)} chars - PASS")

    # Test Skills Store
    print("\n--- Skills Store ---")
    ss = SkillsStore(Path("standards"))
    ss.load()
    skills = ss.list_all()
    print(f"Total skills loaded: {len(skills)}")
    for s in skills:
        print(f"  [{s.language.value}] {s.id} ({s.stack}) - {s.description[:60]}...")

    # Test query
    csharp_skills = ss.query(language=Language.CSHARP)
    print(f"\nC#/.NET skills: {len(csharp_skills)}")
    stack_skills = ss.query(stack="csharp")
    print(f"Stack=csharp skills: {len(stack_skills)}")

    # Test get by ID
    skill = ss.get("csharp/api-design")
    assert skill is not None, "Should find csharp/api-design"
    print(f"\nGet by ID test: '{skill.name}' - PASS")
    assert len(skill.content) > 100, "Skill content should be substantial"
    print(f"Content length: {len(skill.content)} chars - PASS")

    # Test Audit Store
    print("\n--- Audit Store ---")
    audit = AuditStore()
    audit.record_access("rule", "csharp/naming-conventions", language="csharp")
    audit.record_access("skill", "csharp/api-design")
    audit.record_violation(ViolationReport(
        rule_id="csharp/naming-conventions",
        file_path="test/Example.cs",
        description="Test violation",
        severity=Severity.MEDIUM,
    ))
    stats = audit.get_access_stats()
    print(f"Accesses recorded: {stats['total_accesses']}")
    print(f"Violations recorded: {stats['total_violations']}")
    violations = audit.get_violations()
    assert len(violations) == 1, "Should have 1 violation"
    print("Audit store test - PASS")

    # Test reload
    print("\n--- Reload Test ---")
    rs.reload()
    ss.reload()
    print(f"After reload: {len(rs.list_all())} rules, {len(ss.list_all())} skills - PASS")

    print("\n" + "=" * 60)
    print(f"ALL TESTS PASSED")
    print(f"  Rules: {len(rules)}")
    print(f"  Skills: {len(skills)}")
    print("=" * 60)


def test_server_tools():
    """Test that the MCP server tools work correctly."""
    print("\n--- Server Tools Test ---")
    from standards_server.server import (
        _init_stores,
        get_coding_standards,
        get_rules,
        get_skill,
        list_available_standards,
        report_violation,
        get_compliance_report,
        get_usage_analytics,
        reload_standards,
    )
    _init_stores(Path("standards"))

    # Test get_coding_standards (gateway tool)
    result = get_coding_standards("csharp", "generate")
    assert "MANDATORY" in result, "get_coding_standards should include MANDATORY header"
    assert "Naming Conventions" in result, "get_coding_standards should include rules"
    print("  get_coding_standards(csharp, generate) - PASS")

    result = get_coding_standards("csharp", "review")
    assert "MANDATORY" in result
    print("  get_coding_standards(csharp, review) - PASS")

    result = get_coding_standards("csharp", "refactor")
    assert "MANDATORY" in result
    print("  get_coding_standards(csharp, refactor) - PASS")

    # Test language aliases
    for alias in ["c#", "cs", ".net", "dotnet", "CSharp", "C#", "c-sharp"]:
        result = get_coding_standards(alias, "generate")
        assert "MANDATORY" in result, f"Alias '{alias}' should resolve to csharp"
    print("  get_coding_standards(aliases) - PASS")

    # Test get_rules
    result = get_rules("csharp", "naming")
    assert "Naming Conventions" in result, "get_rules should return naming rules"
    print("  get_rules(csharp, naming) - PASS")

    result = get_rules("csharp", "all")
    assert "Error Handling" in result, "get_rules(all) should include error handling"
    print("  get_rules(csharp, all) - PASS")

    # Test get_skill
    result = get_skill("csharp/api-design")
    assert "not found" not in result.lower(), "get_skill should find csharp/api-design"
    print("  get_skill(csharp/api-design) - PASS")

    result = get_skill("api")  # fuzzy search
    assert "not found" not in result.lower()
    print("  get_skill(api) fuzzy search - PASS")

    # Test list_available_standards
    result = list_available_standards()
    assert "csharp/naming-conventions" in result or "Naming Conventions" in result
    assert "csharp/api-design" in result or "API Design" in result
    print("  list_available_standards() - PASS")

    # Test report_violation
    result = report_violation("csharp/naming-conventions", "test.cs", "Bad name", "high")
    assert "recorded" in result.lower()
    print("  report_violation() - PASS")

    # Test get_compliance_report
    result = get_compliance_report()
    assert "Compliance Report" in result
    print("  get_compliance_report() - PASS")

    # Test get_usage_analytics
    result = get_usage_analytics()
    assert "Usage Analytics" in result
    print("  get_usage_analytics() - PASS")

    # Test reload_standards
    result = reload_standards()
    assert "Rules loaded" in result
    assert "Skills loaded" in result
    print("  reload_standards() - PASS")

    print("\n  All server tools working correctly!")


if __name__ == "__main__":
    test_stores()
    test_server_tools()
