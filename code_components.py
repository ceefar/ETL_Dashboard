import streamlit as st

# ---- code snippet components for portfolio/dev mode ----


# ---- streamlit html/css componenets ----

TEST_CARD_HTML = """
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
background-color: #f7f8fc;
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
<img src="https://c0.wallpaperflare.com/preview/483/210/436/car-green-4x4-jeep.jpg" alt="rover" />
</div>
<div class="card-body">
<span class="tag tag-teal">Technology</span>
<h4>
    Why is the Tesla Cybertruck designed the way it
    is?
</h4>
<p>
    An exploration into the truck's polarising design
</p>
<div class="user">
    <img src="https://yt3.ggpht.com/a/AGF-l7-0J1G0Ue0mcZMw-99kMeVuBmRxiPjyvIYONg=s900-c-k-c0xffffffff-no-rj-mo" alt="user" />
    <div class="user-info">
    <h5>July Dec</h5>
    <small>2h ago</small>
    </div>
</div>
</div>
</div>
<div class="card">
<div class="card-header">
<img src="https://www.newsbtc.com/wp-content/uploads/2020/06/mesut-kaya-LcCdl__-kO0-unsplash-scaled.jpg" alt="ballons" />
</div>
<div class="card-body">
<span class="tag tag-purple">Popular</span>
<h4>
    How to Keep Going When You Don’t Know What’s Next
</h4>
<p>
    The future can be scary, but there are ways to
    deal with that fear.
</p>
<div class="user">
    <img src="https://lh3.googleusercontent.com/ogw/ADGmqu8sn9zF15pW59JIYiLgx3PQ3EyZLFp5Zqao906l=s32-c-mo" alt="user" />
    <div class="user-info">
    <h5>Eyup Ucmaz</h5>
    <small>Yesterday</small>
    </div>
</div>
</div>
</div>
<div class="card">
<div class="card-header">
<img src="https://images6.alphacoders.com/312/thumb-1920-312773.jpg" alt="city" />
</div>
<div class="card-body">
<span class="tag tag-pink">Design</span>
<h4>
    10 Rules of Dashboard Design
</h4>
<p>
    Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
quia. Quo neque error repudiandae fuga?
</p>
<div class="user">
    <img src="https://studyinbaltics.ee/wp-content/uploads/2020/03/3799Ffxy.jpg" alt="user" />
    <div class="user-info">
    <h5>Carrie Brewer</h5>
    <small>1w ago</small>
    </div>
</div>
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
background-color: var(--veryLightGray);
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
margin-bottom: 50px;
margin-top: 100px;
}}
.header p {{
margin: 0 auto;
line-height: 2;
color: var(--grayishBlue);
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
    width: 20%;
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
<h1><b>Your Insights, in a glance</b></h1>
<p style="margin-bottom:15px"><b><span style="color:#555555;">{0}</span></b></p>

<p>Take action without the effort with this easy to digest snapshot which showcases key insights from the data you've selected, don't forget to hit the tabs to discover more</p>
</div>
<div class="row1-container">
<div class="box box-down cyan">
<h2>{1}<br>{2} on fire!</h2>
<p>{3}x over the standard deviation in average product sales per hour</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/hot-sale_64.png" alt=""> 
</div>

<div class="box red">
<h2>{6} {8}</h2>
<p>These hours drastically outperformed the average hourly sales by {7} (volume)... </p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/increase_64.png" alt="">
</div>

<div class="box box-down blue">
<h2>{9} Sales Per Hour</h2>
<p>I'd raise a cup to that</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/sales_64.png" alt="">
</div>
</div>
<div class="row2-container">
<div class="box orange">
<h2>{4:.0f} cups sold</h2>
<p>For a total revenue of ${5:.2f}</p>
<img src="https://thehardgainerbible.com/wp-content/uploads/2022/07/coffee-cup_64.png" alt="">
</div>
</div>
</body>
</html>
"""
#stc.html(TEST_CARD_HTML_2.format(), height=1500)



# sumnt we're seeing rapid growth
# <h2>{0} Is Highly Popular</h2>
# <p>At {0} we're seeing {1}x the standard deviation in sales for {2}</p>
# are all performing strongly, and are over the average hourly sales<br>- Make sure dedicated staff are available during these hours
# ACTIONABLE INSIGHT TO BE SOMETHING LIKE A 5P INCREASE ON THIS ITEM WILL BE ENTIRE UNNOTICED BY CUSTOMERS BUT WILL GENERATE SIGNIFICANT REVENUE???? (sim)
# INSIGHTS LIKE - consider bundling this items a these times for upsell potential



# https://assets.codepen.io/2301174/icon-supervisor.svg