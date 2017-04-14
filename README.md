# workday
parse workday job postings


## User Guide

`pip install -r requirements.txt`

and then

`python3 workday.py comapny_name`

or

`workday = WorkdayCrawler()`
`workday.get_by_company('the company name')`

The json output will be simililar to cornell.json:

{'cornell': [{'title': 'president', description:'So cool', 'url':'https://cornell.workdayjob.com......'}]}

## How it works

1. Search on Google with key words `myworkdayjobs.com` and the company name
2. parse google response to get the first matching result
3. Use the result url to read the job posting landing page's async api call
4. Parse (3) to get all the posts' url (incuding paginations)
5. Get all the json responses by calling (4)
6. Parse (5) to get the job details
7. Store all the details in <<company_name>>.json
