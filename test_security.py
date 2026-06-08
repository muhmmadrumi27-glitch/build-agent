"""Tests for Security Module."""
import pytest
from security import (
    AuditLogger,
    PermissionManager,
    SecurityPolicy,
    create_access_token,
    decode_access_token,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    hash_password,
    mask_sensitive_data,
    verify_password,
)


class TestPasswordSecurity:
    """Test suite for password security."""

    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestJWT:
    """Test suite for JWT tokens."""

    def test_token_creation(self):
        """Test JWT token creation."""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_decode(self):
        """Test JWT token decoding."""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"

    def test_invalid_token(self):
        """Test invalid token handling."""
        decoded = decode_access_token("invalid_token")
        assert decoded is None


class TestEncryption:
    """Test suite for encryption."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        original = "sensitive_data_123"
        encrypted = encrypt_sensitive_data(original)

        assert encrypted != original
        assert len(encrypted) > 0

        decrypted = decrypt_sensitive_data(encrypted)
        assert decrypted == original

    def test_mask_sensitive_data(self):
        """Test data masking."""
        data = "password123"
        masked = mask_sensitive_data(data, visible_chars=4)

        assert masked.endswith("123")
        assert masked.startswith("*")
        assert len(masked) == len(data)


class TestSecurityPolicy:
    """Test suite for SecurityPolicy."""

    def test_validate_safe_command(self):
        """Test validating safe command."""
        valid, error = SecurityPolicy.validate_command("ls -la")
        assert valid is True
        assert error is None

    def test_validate_dangerous_command(self):
        """Test validating dangerous command."""
        valid, error = SecurityPolicy.validate_command("rm -rf /")
        assert valid is False
        assert error is not None

    def test_validate_file_access_safe(self):
        """Test validating safe file access."""
        valid, error = SecurityPolicy.validate_file_access("/tmp/test.txt")
        assert valid is True

    def test_validate_file_access_sensitive(self):
        """Test validating sensitive file access."""
        valid, error = SecurityPolicy.validate_file_access("/home/user/.ssh/id_rsa")
        assert valid is False

    def test_validate_url_safe(self):
        """Test validating safe URL."""
        valid, error = SecurityPolicy.validate_url("https://example.com")
        assert valid is True

    def test_validate_url_blocked(self):
        """Test validating blocked URL."""
        valid, error = SecurityPolicy.validate_url("https://malware-site.com")
        assert valid is False

    def test_validate_action(self):
        """Test action validation."""
        valid, error, metadata = SecurityPolicy.validate_action(
            "mouse_click",
            {"x": 100, "y": 200},
        )
        assert valid is True


class TestAuditLogger:
    """Test suite for AuditLogger."""

    def test_log_security_event(self):
        """Test logging security event."""
        # Should not raise
        AuditLogger.log_security_event(
            event_type="test_event",
            details={"key": "value"},
            severity="low",
        )

    def test_log_action(self):
        """Test logging action."""
        # Should not raise
        AuditLogger.log_action(
            action_type="mouse_click",
            parameters={"x": 100},
            result="success",
        )


class TestPermissionManager:
    """Test suite for PermissionManager."""

    def test_admin_permissions(self):
        """Test admin role permissions."""
        assert PermissionManager.has_permission("admin", "user:create") is True
        assert PermissionManager.has_permission("admin", "task:delete") is True

    def test_user_permissions(self):
        """Test user role permissions."""
        assert PermissionManager.has_permission("user", "task:create") is True
        assert PermissionManager.has_permission("user", "user:delete") is False

    def test_viewer_permissions(self):
        """Test viewer role permissions."""
        assert PermissionManager.has_permission("viewer", "session:read") is True
        assert PermissionManager.has_permission("viewer", "task:create") is False

    def test_invalid_role(self):
        """Test invalid role."""
        assert PermissionManager.has_permission("invalid", "task:create") is False
