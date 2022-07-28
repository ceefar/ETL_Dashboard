import streamlit as st

# ---- code snippet components for portfolio/dev mode ----


# ---- streamlit html/css componenets ----

THREE_CARD_INFO = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Roboto&display=swap");
* {{
box-sizing: border-box;
}}
body {{
display: flex;
justify-content: center;
align-items: center;
margin: 0;
font-family: "Roboto", sans-serif;
color: #10182f;
}}
.container {{
display: flex;
width: 1040px;
justify-content: space-evenly;
flex-wrap: wrap;
}}
.card {{
margin: 10px;
background-color: #fff;
border-radius: 10px;
box-shadow: 0 2px 20px rgba(0, 0, 0, 0.2);
overflow: hidden;
width: 300px;
}}
.card-header img {{
width: 100%;
height: 200px;
object-fit: cover;
}}
.card-body {{
display: flex;
flex-direction: column;
justify-content: center;
align-items: flex-start;
padding: 20px;
min-height: 250px;
}}
.tag {{
background: #cccccc;
border-radius: 50px;
font-size: 12px;
margin: 0;
color: #fff;
padding: 2px 10px;
text-transform: uppercase;
cursor: pointer;
}}
.tag-teal {{
background-color: #47bcd4;
}}
.tag-purple {{
background-color: #5e76bf;
}}
.tag-pink {{
background-color: #cd5b9f;
}}
.card-body p {{
font-size: 13px;
margin: 0 0 40px;
}}
.user {{
display: flex;
margin-top: auto;
}}
.user img {{
border-radius: 50%;
width: 40px;
height: 40px;
margin-right: 10px;
}}
.user-info h5 {{
margin: 0;
}}
.user-info small {{
color: #545d7a;
}}
</style>

<div class="container">
<div class="card">
<div class="card-header">
<img src="https://nmgprod.s3.amazonaws.com/media/files/86/53/8653b96f15861cf643cc136bf94db701/cover_image_1587766077.jpg.760x400_q85_crop_upscale.jpg" alt="money" />
</div>
<div class="card-body">
<span class="tag tag-teal">Popularity Insights</span>
<h4>
    What's Hot - Top Sellers & Averages
</h4>
<p>
    By using average sales @ {0:.0f} cups as a baseline, we can see that but the hours {1} performed over the average.
    <br><br>But the true top {7} {2}, with {3:.0f} additional sales/volume over the average {8} for a total of ${4:.2f} over the average, or ${5:.2f} in total revenue over the period.
    <br><br>That performance is {6:.0f} times over the standard deviation in terms of volume and should be monitored for future opportunities. 
</p>

</div>
</div>
<div class="card">
<div class="card-header">
<img src="https://www.allbusiness.com/asset/2019/05/Business-time-management-..jpg" alt="time" />
</div>
<div class="card-body">
<span class="tag tag-purple">Stats Breakdown</span>
<h4>
    Tick Tock - Hourly Statistical Analysis 
</h4>
<p>
    Here's some hourly stats...<br><br>
    {9}
    <br><br>
    <i>SD = Standard Deviation</i>
</p>

</div>
</div>
<div class="card">
<div class="card-header">
<img src="https://cff2.earth.com/uploads/2017/10/20195551/Climate-change-could-devastate-the-coffee-industry-850x500.jpg" alt="coffee" />
</div>
<div class="card-body">
<span class="tag tag-teal">Popularity Insights</span>
<h4>
    Cooling Off - Areas To Improve
</h4>
<p>
    Top performers aren't the only thing that matters. Here are some areas could use improvement that you should focus to maximise profits.<br><br>
    {10} {11} {12} {13}
</p>

</div>
</div>

"""    


#stc.html(TEST_CARD_HTML.format(), height=500)


FOUR_CARD_INFO = """

<style>
:root {{
--red: hsl(0, 78%, 62%);
--cyan: hsl(180, 62%, 55%);
--orange: hsl(34, 97%, 64%);
--blue: hsl(212, 86%, 64%);
--varyDarkBlue: hsl(234, 12%, 34%);
--grayishBlue: hsl(229, 6%, 66%);
--veryLightGray: hsl(0, 0%, 98%);
--weight1: 200;
--weight2: 400;
--weight3: 600;
}}
body {{
font-size: 15px;
font-family: 'Poppins', sans-serif;
}}
.attribution {{ 
font-size: 11px; text-align: center; 
}}
.attribution a {{ 
color: hsl(228, 45%, 44%); 
}}
h1:first-of-type {{
font-weight: var(--weight1);
color: var(--varyDarkBlue);
margin-bottom:5px;
}}
h1:last-of-type {{
color: var(--varyDarkBlue);
}}
@media (max-width: 400px) {{
h1 {{
    font-size: 1.5rem;
}}
}}
.header {{
text-align: center;
line-height: 0.8;
margin-bottom: 20px;
margin-top: 40px;
}}
.header p {{
margin: 0 auto;
line-height: 2;
color: var(--grayishBlue);
font-size: 1.2rem;
}}
.box p {{
color: var(--grayishBlue);
}}
.box {{
border-radius: 5px;
box-shadow: 0px 30px 40px -20px var(--grayishBlue);
padding: 30px;
margin: 20px;  
}}
img {{
float: right;
}}
@media (max-width: 450px) {{
.box {{
    height: 200px;
}}
}}
@media (max-width: 950px) and (min-width: 450px) {{
.box {{
    text-align: center;
    height: 180px;
}}
}}
.cyan {{
border-top: 3px solid var(--cyan);
}}
.red {{
border-top: 3px solid var(--red);
}}
.blue {{
border-top: 3px solid var(--blue);
}}
.orange {{
border-top: 3px solid var(--orange);
}}
h2 {{
color: var(--varyDarkBlue);
font-weight: var(--weight3);
}}
@media (min-width: 950px) {{
.row1-container {{
    display: flex;
    justify-content: center;
    align-items: center;
}}
.row2-container {{
    display: flex;
    justify-content: center;
    align-items: center;
}}
.box-down {{
    position: relative;
    top: 150px;
}}
.box {{
    width: 25%;
}}
.header p {{
    width: 30%;
}}
}}


</style>

<!DOCTYPE html>
<html lang="en">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="styles.css">
<link
href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,200;0,400;0,600;1,200;1,400;1,600&display=swap"
rel="stylesheet">
</head>

<body>

<div class="header">
<p><b><span style="color:#555555;">{9}</span></b></p>
</div>

<div class="row1-container">

<div class="box box-down cyan">
<h2>{3:.0f} cups sold</h2>
<p>For a total revenue of ${4:.2f}</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/sales_64.png" alt="">
</div>

<div class="box red">
<h2>{5} {7}</h2>
<p>These hours drastically outperformed the average hourly sales (volume) by {6} cups sold respectively... </p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/fighting-game_64.png" alt="">
</div>

<div class="box box-down blue">
<h2>{8:.0f} sales per hour</h2>
<p>Raise a paper cup to strong average hourly sales</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/coffee-cup_64.png" alt="">
</div>

</div>

<div class="row2-container">

<div class="box orange">
<h2>{0}<br>{1} on fire!</h2>
<p>{2}x over the standard deviation in average product sales per hour</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/hot-sale_64.png" alt=""> 
</div>

</div>

</body>
</html>
"""
#stc.html(TEST_CARD_HTML_2.format(), height=1500)

#style="margin-top:40px"

# sumnt we're seeing rapid growth
# <h2>{0} Is Highly Popular</h2>
# <p>At {0} we're seeing {1}x the standard deviation in sales for {2}</p>
# are all performing strongly, and are over the average hourly sales<br>- Make sure dedicated staff are available during these hours
# ACTIONABLE INSIGHT TO BE SOMETHING LIKE A 5P INCREASE ON THIS ITEM WILL BE ENTIRE UNNOTICED BY CUSTOMERS BUT WILL GENERATE SIGNIFICANT REVENUE???? (sim)
# INSIGHTS LIKE - consider bundling this items a these times for upsell potential



# https://assets.codepen.io/2301174/icon-supervisor.svg