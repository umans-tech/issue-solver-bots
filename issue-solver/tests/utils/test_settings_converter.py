"""Tests for settings_converter module."""

from pathlib import Path
from typing import Optional

import pytest
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver.utils.settings_converter import settings_to_env_string


class SimpleSettings(BaseSettings):
    """Simple flat settings for testing."""
    name: str = "test"
    count: int = 42
    enabled: bool = True
    path: Optional[Path] = None
    url: Optional[AnyUrl] = None


class NestedChildSettings(BaseSettings):
    """Nested child settings."""
    host: str = "localhost"
    port: int = 5432
    ssl: bool = False


class NestedParentSettings(BaseSettings):
    """Parent settings with nested child."""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    app_name: str = "myapp"
    debug: bool = False
    database: NestedChildSettings = Field(default_factory=NestedChildSettings)


class PrefixedSettings(BaseSettings):
    """Settings with env_prefix."""
    model_config = SettingsConfigDict(
        env_prefix="MYAPP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    api_key: str = "secret"
    timeout: int = 30


class PrefixedNestedSettings(BaseSettings):
    """Parent with prefix and nested child with prefix."""
    model_config = SettingsConfigDict(
        env_prefix="PARENT_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    name: str = "parent"
    child: PrefixedSettings = Field(default_factory=PrefixedSettings)


class SpecialValuesSettings(BaseSettings):
    """Settings with special values that need careful formatting."""
    string_with_spaces: str = "hello world"
    string_with_quotes: str = 'say "hello"'
    path_with_spaces: Path = Path("/path with spaces/file.txt")
    url_example: AnyUrl = AnyUrl("https://example.com/path?param=value")
    none_value: Optional[str] = None
    empty_string: str = ""
    zero_value: int = 0
    false_value: bool = False


class SolveCommandLikeSettings(BaseSettings):
    """Settings similar to SolveCommand for realistic testing."""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    issue: str = "Fix the bug"
    agent: str = "swe-agent"
    ai_model: str = "gpt-4o-mini"
    ai_model_version: Optional[str] = None
    repo_path: Path = Path(".")
    process_id: Optional[str] = None
    database_url: Optional[str] = None
    redis_url: Optional[str] = None


class GitLikeSettings(BaseSettings):
    """Settings similar to GitSettings for nested testing."""
    repository_url: str = "https://github.com/user/repo.git"
    access_token: str = "ghp_token123"
    user_mail: str = "agent@umans.ai"
    user_name: str = "Umans Agent"


class SolveCommandWithGitSettings(BaseSettings):
    """Combined settings with nested Git settings."""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    issue: str = "Fix the bug"
    agent: str = "swe-agent"
    git: GitLikeSettings = Field(default_factory=GitLikeSettings)


class PrepareCommandLikeSettings(BaseSettings):
    """Settings similar to PrepareCommand."""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    process_id: str = "proc-123"
    repo_path: Path = Path("/workspace/repo")
    url: str = "https://github.com/user/repo.git"
    access_token: str = "ghp_token456"
    install_script: Path = Path("./install.sh")


class TestSimpleFlatSettings:
    """Test cases for simple flat settings."""
    
    def test_given_simple_settings_when_converting_then_returns_flat_env_vars(self):
        # Given
        settings = SimpleSettings(
            name="myapp",
            count=100,
            enabled=True
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "COUNT=100",
            "ENABLED=true",
            "NAME=myapp"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_settings_with_none_values_when_converting_then_skips_none_values(self):
        # Given
        settings = SimpleSettings(
            name="test",
            count=42,
            enabled=False,
            path=None,
            url=None
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "COUNT=42",
            "ENABLED=false",
            "NAME=test"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_settings_with_path_and_url_when_converting_then_formats_correctly(self):
        # Given
        settings = SimpleSettings(
            name="test",
            count=1,
            enabled=True,
            path=Path("/home/user/file.txt"),
            url=AnyUrl("https://api.example.com/v1")
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "COUNT=1",
            "ENABLED=true",
            "NAME=test",
            "PATH=/home/user/file.txt",
            "URL=https://api.example.com/v1"
        ]
        assert result == "\n".join(expected_lines)


class TestNestedSettings:
    """Test cases for nested settings."""
    
    def test_given_nested_settings_when_converting_then_uses_delimiter(self):
        # Given
        child = NestedChildSettings(host="db.example.com", port=3306, ssl=True)
        settings = NestedParentSettings(
            app_name="webapp",
            debug=True,
            database=child
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "APP_NAME=webapp",
            "DATABASE__HOST=db.example.com",
            "DATABASE__PORT=3306",
            "DATABASE__SSL=true",
            "DEBUG=true"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_empty_nested_settings_when_converting_then_handles_gracefully(self):
        # Given
        settings = NestedParentSettings()
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "APP_NAME=myapp",
            "DATABASE__HOST=localhost",
            "DATABASE__PORT=5432",
            "DATABASE__SSL=false",
            "DEBUG=false"
        ]
        assert result == "\n".join(expected_lines)


class TestPrefixedSettings:
    """Test cases for settings with env_prefix."""
    
    def test_given_prefixed_settings_when_converting_then_adds_prefix(self):
        # Given
        settings = PrefixedSettings(
            api_key="sk-123456",
            timeout=60
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "MYAPP_API_KEY=sk-123456",
            "MYAPP_TIMEOUT=60"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_prefixed_nested_settings_when_converting_then_combines_prefixes(self):
        # Given
        child = PrefixedSettings(api_key="nested-key", timeout=45)
        settings = PrefixedNestedSettings(
            name="parent-app",
            child=child
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "PARENT_CHILD__MYAPP_API_KEY=nested-key",
            "PARENT_CHILD__MYAPP_TIMEOUT=45",
            "PARENT_NAME=parent-app"
        ]
        assert result == "\n".join(expected_lines)


class TestSpecialValueFormatting:
    """Test cases for special value formatting."""
    
    def test_given_strings_with_spaces_when_converting_then_quotes_them(self):
        # Given
        settings = SpecialValuesSettings(
            string_with_spaces="hello world test",
            string_with_quotes="normal",
            path_with_spaces=Path("/normal/path"),
            url_example=AnyUrl("https://example.com"),
            empty_string="",
            zero_value=5,
            false_value=True
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "EMPTY_STRING=",
            "FALSE_VALUE=true",
            "PATH_WITH_SPACES=/normal/path",
            "STRING_WITH_QUOTES=normal",
            "STRING_WITH_SPACES=\"hello world test\"",
            "URL_EXAMPLE=https://example.com",
            "ZERO_VALUE=5"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_strings_with_quotes_when_converting_then_escapes_quotes(self):
        # Given
        settings = SpecialValuesSettings(
            string_with_quotes='He said "Hello World"',
            string_with_spaces="normal",
            path_with_spaces=Path("/path with spaces/file.txt"),
            url_example=AnyUrl("https://example.com"),
            empty_string="value",
            zero_value=1,
            false_value=False
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "EMPTY_STRING=value",
            "FALSE_VALUE=false",
            "PATH_WITH_SPACES=\"/path with spaces/file.txt\"",
            "STRING_WITH_QUOTES=\"He said \\\"Hello World\\\"\"",
            "STRING_WITH_SPACES=normal",
            "URL_EXAMPLE=https://example.com",
            "ZERO_VALUE=1"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_boolean_values_when_converting_then_formats_as_lowercase(self):
        # Given
        settings = SpecialValuesSettings(
            false_value=True,
            string_with_spaces="test",
            string_with_quotes="test",
            path_with_spaces=Path("/test"),
            url_example=AnyUrl("https://example.com"),
            empty_string="test",
            zero_value=1
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        assert "FALSE_VALUE=true" in result
        
        # Test with False
        settings.false_value = False
        result = settings_to_env_string(settings)
        assert "FALSE_VALUE=false" in result


class TestRealisticScenarios:
    """Test cases based on actual SolveCommand and PrepareCommand settings."""
    
    def test_given_solve_command_like_settings_when_converting_then_matches_expected_format(self):
        # Given
        settings = SolveCommandLikeSettings(
            issue="Implement user authentication",
            agent="claude-code",
            ai_model="claude-3-sonnet",
            ai_model_version="20241022",
            repo_path=Path("/workspace/myapp"),
            process_id="proc-uuid-123",
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/0"
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "AGENT=claude-code",
            "AI_MODEL=claude-3-sonnet",
            "AI_MODEL_VERSION=20241022",
            "DATABASE_URL=postgresql://user:pass@localhost/db",
            "ISSUE=\"Implement user authentication\"",
            "PROCESS_ID=proc-uuid-123",
            "REDIS_URL=redis://localhost:6379/0",
            "REPO_PATH=/workspace/myapp"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_solve_command_with_git_settings_when_converting_then_handles_nested_correctly(self):
        # Given
        git_settings = GitLikeSettings(
            repository_url="https://github.com/umans-ai/issue-solver.git",
            access_token="ghp_secrettoken123",
            user_mail="bot@umans.ai",
            user_name="Umans Bot"
        )
        settings = SolveCommandWithGitSettings(
            issue="Fix critical bug",
            agent="swe-agent",
            git=git_settings
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "AGENT=swe-agent",
            "GIT__ACCESS_TOKEN=ghp_secrettoken123",
            "GIT__REPOSITORY_URL=https://github.com/umans-ai/issue-solver.git",
            "GIT__USER_MAIL=bot@umans.ai",
            "GIT__USER_NAME=\"Umans Bot\"",
            "ISSUE=\"Fix critical bug\""
        ]
        assert result == "\n".join(expected_lines)
    
    def test_given_prepare_command_like_settings_when_converting_then_formats_correctly(self):
        # Given
        settings = PrepareCommandLikeSettings(
            process_id="prepare-proc-456",
            repo_path=Path("/tmp/workspace/my project"),
            url="https://github.com/user/my-repo.git",
            access_token="pat_github_token",
            install_script=Path("./scripts/install dependencies.sh")
        )
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "ACCESS_TOKEN=pat_github_token",
            "INSTALL_SCRIPT=\"./scripts/install dependencies.sh\"",
            "PROCESS_ID=prepare-proc-456",
            "REPO_PATH=\"/tmp/workspace/my project\"",
            "URL=https://github.com/user/my-repo.git"
        ]
        assert result == "\n".join(expected_lines)


class TestEdgeCases:
    """Test cases for edge cases and error conditions."""
    
    def test_given_empty_settings_when_converting_then_returns_empty_string(self):
        # Given
        class EmptySettings(BaseSettings):
            pass
        
        settings = EmptySettings()
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        assert result == ""
    
    def test_given_settings_with_all_none_values_when_converting_then_returns_empty_string(self):
        # Given
        class AllNoneSettings(BaseSettings):
            value1: Optional[str] = None
            value2: Optional[int] = None
            value3: Optional[bool] = None
        
        settings = AllNoneSettings()
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        assert result == ""
    
    def test_given_complex_string_with_special_characters_when_converting_then_escapes_correctly(self):
        # Given
        class SpecialStringSettings(BaseSettings):
            complex_string: str = 'Value with "quotes" and spaces and\nnewlines'
        
        settings = SpecialStringSettings()
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected = 'COMPLEX_STRING="Value with \\"quotes\\" and spaces and\nnewlines"'
        assert result == expected
    
    def test_given_settings_with_custom_delimiter_when_converting_then_uses_custom_delimiter(self):
        # Given
        class CustomDelimiterSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_nested_delimiter="___",
                env_file=".env",
                env_file_encoding="utf-8",
                extra="ignore",
            )
            
            parent_value: str = "parent"
            child: NestedChildSettings = Field(default_factory=NestedChildSettings)
        
        settings = CustomDelimiterSettings()
        
        # When
        result = settings_to_env_string(settings)
        
        # Then
        expected_lines = [
            "CHILD___HOST=localhost",
            "CHILD___PORT=5432",
            "CHILD___SSL=false",
            "PARENT_VALUE=parent"
        ]
        assert result == "\n".join(expected_lines)