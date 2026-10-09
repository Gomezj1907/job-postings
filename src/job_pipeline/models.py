from dataclasses import dataclass


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