import csv
from jobspy import scrape_jobs


def job_scrapper(site_name=["indeed", "linkedin", "zip_recruiter", "google"],search_term="software engineer",country_indeed="India",location="India",results_wanted=20,hours_old=72,google_search_term="software engineer jobs near Bengaluru, India since yesterday"):

  jobs = scrape_jobs(
    site_name=site_name, # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term=search_term,    
    google_search_term=google_search_term,
    location="India",
    results_wanted=20,
    hours_old=72,
    country_indeed='India',
    
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
  )
  print(f"Found {len(jobs)} jobs")
  print(jobs.head())
  jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
  return jobs