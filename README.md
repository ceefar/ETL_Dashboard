## ETL_Dashboard  
  
This is still massively in development, but you (should) be able to check it out over on Streamlit Cloud [ETL Web App](https://ceefar-etl-dashboard-app-insights-7xqywv.streamlitapp.com/)  
*(again please note this is in development right now, and so it's current state my be unstable - a solid state version can be provided on request)*  
  
#### What is this?  
Personal Project [In Progress] - Insights focused web app (using streamlit) for the data from my group project, developing further as many things I didn't get to do (over the 6 weeks of the group project).   
is actually one of many versions of the dashboard, though porting to a MySQL DB (one I host myself) as trials are expiring - hence why this will take some time (so focusing on getting one web app page to mvp level at a time)  
    
#### What was the ETL?  
Should note that previous the ETL was hosted on AWS, utilising ** AWS S3** buckets to store raw data, **AWS Lambda** to automate and run the ETL code as data is received, **AWS Redshift** to store the data (using a variant of PostgreSQL), and finally further storing the data in a **Snowflake Data Warehouse**.   
Final dataset was over 1,000,000 (1m) datapoints (approx 5 stores of data, per day), has 100% completeness (based on data provided, tho some days were missing due to errors in the courses dataset creator)  
  
#### More Info Coming Soon    
Yes I will write this readme - with all the relevant info shortly, i swear   
  
  
![Ceefar's GitHub stats](https://github-readme-stats.vercel.app/api?username=ceefar&show_icons=true&theme=gruvbox)
