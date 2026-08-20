import json
from pathlib import Path


class Memory:

    def __init__(
        self,
        path=None
    ):
        default_path = Path(__file__).resolve().parents[1] / "memory" / "user_profile.json"
        self.path = Path(path).expanduser().resolve() if path else default_path

    def load(self):

        if not self.path.exists():
            return {
                "major": "",
                "education": "",
                "target_jobs": "",
                "experience": "",
                "ai_experience": ""
            }

        with open(
            self.path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def save(self, data):

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    def update(self, updates):

        profile = self.load()

        for key, value in updates.items():

            if value:
                profile[key] = value

        self.save(profile)

        return profile
