def normalize_roles(raw_roles: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []

    for role in raw_roles:
        value = role.strip().lower()

        if not value:
            raise ValueError("role entries must not be blank")

        if value not in normalized:
            normalized.append(value)

    return tuple(normalized)
