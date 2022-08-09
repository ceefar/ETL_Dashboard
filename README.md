## ETL_Dashboard  
  
**Check out the pre-MVP webapp over on Streamlit Cloud [ETL Web App](https://ceefar-etl-dashboard-app-insights-7xqywv.streamlitapp.com/)  **
   
##### Landing Preview   
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/08/insights_dash_1.png" width="800">  
   
##### Dynamic User Selection & HTML Card Components  
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/08/insights_dash_2.png" width="400"><img src="https://thehardgainerbible.com/wp-content/uploads/2022/08/insights_dash_3.png" width="400">  
  
##### NEW - Portfolio Mode   
Take a peek at the backend and watch live code update the sql queries as you change inputs  
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/08/insights_dash_6.png" width="400"><img src="https://thehardgainerbible.com/wp-content/uploads/2022/08/insights_dash_8.png" width="400">  
   

*(again please note this is in development right now, and so it's current state my be somewhat unstable)*  
  
#### What is this?  
Personal Project [In Progress] - Insights focused web app (using streamlit) for the data from my group project, developing further as many things I didn't get to do (over the 6 weeks of the group project).   
is actually one of many versions of the dashboard, though porting to a MySQL DB (one I host myself) as trials are expiring - hence why this will take some time (so focusing on getting one web app page to mvp level at a time)  
    
#### What was the ETL?  
Should note that previous the ETL was hosted on AWS, utilising ** AWS S3** buckets to store raw data, **AWS Lambda** to automate and run the ETL code as data is received, **AWS Redshift** to store the data (using a variant of PostgreSQL), and finally further storing the data in a **Snowflake Data Warehouse**.   
Final dataset was over 1,000,000 (1m) datapoints (approx 5 stores of data, per day), has 100% completeness (based on data provided, tho some days were missing due to errors in the courses dataset creator)  
  
#### More Info Coming Soon    
Yes I will write this readme - with all the relevant info shortly, i swear   
  
  
![Ceefar's GitHub stats](https://github-readme-stats.vercel.app/api?username=ceefar&show_icons=true&theme=gruvbox)
