from packages.common.errors import APIError, DomainError, ErrorCode, ErrorEnvelope


def test_api_error_serializes_to_expected_shape() -> None:
    error = APIError(
        code=ErrorCode.POLICY_DENIED,
        message="This request cannot be completed in the current context.",
        trace_id="trace_789",
    )

    assert error.model_dump(mode="json") == {
        "code": "POLICY_DENIED",
        "message": "This request cannot be completed in the current context.",
        "trace_id": "trace_789",
    }


def test_error_envelope_matches_documented_api_shape() -> None:
    envelope = ErrorEnvelope(
        error=APIError(
            code=ErrorCode.POLICY_DENIED,
            message="This request cannot be completed in the current context.",
            trace_id="trace_789",
        )
    )

    assert envelope.model_dump(mode="json") == {
        "error": {
            "code": "POLICY_DENIED",
            "message": "This request cannot be completed in the current context.",
            "trace_id": "trace_789",
        }
    }


def test_domain_error_converts_to_safe_api_envelope() -> None:
    error = DomainError(
        code=ErrorCode.TENANT_CONTEXT_MISSING,
        message="This request cannot be completed in the current context.",
        trace_id="trace_123",
    )

    assert error.to_envelope().model_dump(mode="json") == {
        "error": {
            "code": "TENANT_CONTEXT_MISSING",
            "message": "This request cannot be completed in the current context.",
            "trace_id": "trace_123",
        }
    }


def test_api_error_rejects_multiline_messages() -> None:
    try:
        APIError(
            code=ErrorCode.INTERNAL_ERROR,
            message="unsafe\nmessage",
            trace_id="trace_999",
        )
    except ValueError as exc:
        assert "single-line" in str(exc)
    else:
        raise AssertionError("Expected APIError validation to reject multiline messages.")


def test_domain_error_keeps_internal_details_out_of_api_payload() -> None:
    error = DomainError(
        code=ErrorCode.INTERNAL_ERROR,
        message="This request cannot be completed in the current context.",
        trace_id="trace_456",
        details={"internal_reason": "stack trace placeholder"},
    )

    assert error.to_envelope().model_dump(mode="json") == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "This request cannot be completed in the current context.",
            "trace_id": "trace_456",
        }
    }
