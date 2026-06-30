def normalize_scopes(raw_scopes: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []

    for scope in raw_scopes:
        value = scope.strip().lower()

        if not value:
            raise ValueError("scope entries must not be blank")

        if value not in normalized:
            normalized.append(value)

    return tuple(normalized)
