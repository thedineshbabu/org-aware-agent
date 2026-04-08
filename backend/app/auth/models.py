from dataclasses import dataclass, field


@dataclass
class UserContext:
    user_id: str
    email: str
    display_name: str
    roles: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    department: str = ""

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def to_prompt_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "department": self.department,
            "roles": ", ".join(self.roles) if self.roles else "employee",
            "groups": ", ".join(self.groups) if self.groups else "none",
        }
