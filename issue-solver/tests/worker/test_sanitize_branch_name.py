from issue_solver.git_operations.git_helper import sanitize_branch_name


def test_sanitize_empty_string():
    """Empty string should return 'resolution'."""
    assert sanitize_branch_name("") == "resolution"


def test_sanitize_whitespace_only():
    """Whitespace-only string should return 'resolution'."""
    assert sanitize_branch_name("   ") == "resolution"


def test_sanitize_none_input():
    """None input should return 'resolution'."""
    assert sanitize_branch_name(None) == "resolution"


def test_sanitize_basic_valid_name():
    """Basic valid name should remain unchanged."""
    assert sanitize_branch_name("feature-branch") == "feature-branch"


def test_sanitize_spaces_replaced():
    """Spaces should be replaced with hyphens."""
    assert sanitize_branch_name("fix authentication bug") == "fix-authentication-bug"


def test_sanitize_special_characters():
    """Special characters should be replaced with hyphens."""
    assert sanitize_branch_name("Fix: authentication bug") == "Fix-authentication-bug"
    assert sanitize_branch_name("Update README.md?") == "Update-README.md"
    assert sanitize_branch_name("Feature [new] component") == "Feature-new-component"
    assert sanitize_branch_name("Fix~something^weird") == "Fix-something-weird"
    assert sanitize_branch_name("Issue*with*stars") == "Issue-with-stars"


def test_sanitize_consecutive_separators():
    """Consecutive separators should be collapsed to single hyphen."""
    assert sanitize_branch_name("fix--double--dash") == "fix-double-dash"
    assert sanitize_branch_name("fix..double..dots") == "fix-double-dots"
    assert sanitize_branch_name("fix__double__underscore") == "fix-double-underscore"
    assert sanitize_branch_name("fix-.-_mixed") == "fix-mixed"


def test_sanitize_leading_trailing_invalid_chars():
    """Leading/trailing invalid characters should be removed."""
    assert sanitize_branch_name("-leading-dash") == "leading-dash"
    assert sanitize_branch_name("trailing-dash-") == "trailing-dash"
    assert sanitize_branch_name(".leading-dot") == "leading-dot"
    assert sanitize_branch_name("trailing-dot.") == "trailing-dot"
    assert sanitize_branch_name("_leading-underscore") == "leading-underscore"
    assert sanitize_branch_name("trailing-underscore_") == "trailing-underscore"
    assert sanitize_branch_name("trailing-slash/") == "trailing-slash"
    assert sanitize_branch_name("...test...") == "test"


def test_sanitize_length_truncation():
    """Long names should be truncated to 50 characters."""
    long_name = "a" * 60
    result = sanitize_branch_name(long_name)
    assert len(result) <= 50
    assert result == "a" * 50


def test_sanitize_length_truncation_with_trailing_chars():
    """Truncation should not end with invalid characters."""
    # Create a name that would end with invalid chars after truncation
    long_name = "a" * 48 + ".-"
    result = sanitize_branch_name(long_name)
    assert len(result) <= 50
    assert not result.endswith(("-", ".", "_"))


def test_sanitize_complex_real_world_examples():
    """Test with real-world issue title examples."""
    assert (
        sanitize_branch_name("Bug: User can't login with special chars")
        == "Bug-User-can-t-login-with-special-chars"
    )
    assert (
        sanitize_branch_name("Feature Request: Add @mentions support")
        == "Feature-Request-Add-mentions-support"
    )
    assert (
        sanitize_branch_name("Docs: Update API documentation (v2.0)")
        == "Docs-Update-API-documentation-v2.0"
    )
    assert (
        sanitize_branch_name("Fix #123: Resolve authentication issue")
        == "Fix-123-Resolve-authentication-issue"
    )


def test_sanitize_only_invalid_chars():
    """String with only invalid chars should return 'resolution'."""
    assert sanitize_branch_name("?!@#$%^&*()") == "resolution"
    assert sanitize_branch_name("---") == "resolution"
    assert sanitize_branch_name("...") == "resolution"
    assert sanitize_branch_name("___") == "resolution"


def test_sanitize_preserves_valid_chars():
    """Valid characters should be preserved."""
    assert sanitize_branch_name("feature-123_branch.v2") == "feature-123_branch.v2"
    assert sanitize_branch_name("hotfix-2024.01.15") == "hotfix-2024.01.15"


def test_sanitize_unicode_characters():
    """Unicode characters should be replaced with hyphens."""
    assert sanitize_branch_name("Fix café bug") == "Fix-caf-bug"
    assert sanitize_branch_name("Update 中文 docs") == "Update-docs"
