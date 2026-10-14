import re
from dataclasses import dataclass
from datetime import datetime, timedelta

UNIT = {
    "minute": timedelta(minutes=1),
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),   # approximation; LinkedIn's "1 month ago" is fuzzy anyway
}

POSTED = re.compile(r"(\d+)\+?\s+(minute|hour|day|week|month)s?\s+ago")

@dataclass(frozen = True)

class JobCard:
    """ One job as it appears inm the email alert. This is not the same as a JobPosting object, 
    which is a more complete representation of a job. """

    job_id: str  # "4476532843"
    title: str  # "Commercial Data Scientist"
    company: str # "Iron Mountain"
    location: str # "Bogota, D.C."
    insights: tuple[str] # ("This company is actively hiring",)
    source: str  # "job_alert_digest", "jobs_qualification_board", ...
    alert_name: str | None # "Data Scientist in Bogota, D.C."; None for recommendations
    email_id: str  # Gmail message ID it came from

@dataclass(frozen = True)

class JobPosting:

    job_id: str
    company: str
    title: str
    location: str
    posted_raw: str
    fetched_at: datetime
    n_applicants: int | None # not 0 as having 0 is positive, if missing flag it.
    has_applicants_cap: bool 
    workplace: str # On-site, Remote, Hybrid
    employment_type: str # Full-time, Part-time, Contract, Internship, Temporary
    easy_apply: bool
    sector: str
    n_employees: str
    job_description: str

    @property
    def size_min(self) -> int | None:

        nums = re.findall(r"[\d,]+", self.n_employees)
        return int(nums[0].replace(",", "")) if nums else None

    @property
    def posted_at(self) -> datetime | None:

        #handle posted now
        if "just now" in self.posted_raw.lower():
            return self.fetched_at

        time = POSTED.search(self.posted_raw)
        if not time:
            return None
        count, unit = int(time.group(1)), time.group(2)
        return self.fetched_at -count*UNIT[unit]

    @property
    def is_reposted(self) -> bool:
        return "reposted" in self.posted_raw.lower()
    
    