# ---- IMPORTS ----

# for image manipulation
from PIL import Image, ImageDraw, ImageFont, ImageFilter



# ---- DRAW CALENDAR ----

# def highlight_calendar(weeknumb:int, actualweeknumb:int, weekarray:list) -> str:
def highlight_calendar(weeknumb:int, actualweeknumb:int) -> str:
    """ write me pls ceef """

    # set base image to be june or july based on the week number
    if 22 <= actualweeknumb <= 26:
        # open june img as img object
        img = Image.open('imgs/Calendar-2022-June.png')
        # path for the final image
        imgpath = f'imgs/arty/arty_june_{weeknumb}.png'
    else:
        # open july img as img object
        img = Image.open('imgs/Calendar-2022-July.png')   
        # path for the final image
        imgpath = f'imgs/arty/arty_july_{weeknumb}.png' 
        # change weeknumb for july, will start with weeknumb being 5 so -4 as need it to be +1 for offset the highlight for july 
        # as first week is actually the last from june (1st - 3rd)
        weeknumb -= 4

    # setup base object from original bg img and open it for drawing 
    imgDraw = ImageDraw.Draw(img)

    # save the bg before adding rectangle highlight
    img.save(imgpath)

    # ---- start rectangle ----

    # create new draw object with transparency option
    img1 = ImageDraw.Draw(img, "RGBA")

    nudgeVar = 5
    incVar = 90
    n1 = 930 # doesnt change (assuming width)
    n2 = 220
    n3 = 30 # doesnt change (assuming height)
    n4 = 127

    if weeknumb == 1:
        n4 += (incVar * 2) + nudgeVar
    elif weeknumb == 2:
        n2 += incVar
        n4 += (incVar*3) + (nudgeVar*2)
    elif weeknumb == 3:
        n2 += (incVar * 2) + nudgeVar
        n4 += (incVar * 4) + (nudgeVar*2)
    elif weeknumb == 4:    
        n2 += (incVar * 3) + (nudgeVar)
        n4 += (incVar * 5) + (nudgeVar*2)

    # resulting position x dimensions
    # [930, 220, 30, 127]
    # [930, 220, 30, 307]
    # [930, 310, 30, 397]
    # [930, 400, 30, 487]
    # [930, 490, 30, 577]

    # semi-dynamically set the rectangle vars
    rectPos = [n1, n2, n3, n4]
    # draw the rectangle with transparency
    img1.rectangle(rectPos, fill=(34, 139, 34, 55)) # 255, 0, 0 - red | 124, 252, 0 - grass green | 34, 139, 34 - forest green [current]


    # ---- add ticks/crosses ----
    
    tickimg = Image.open("imgs/checked.png")  
    tickimg = tickimg.resize((50, 50))
    tickimg = tickimg.convert("RGBA")

    crossimg = Image.open("imgs/cancel.png")  
    crossimg = crossimg.resize((50, 50))
    crossimg = crossimg.convert("RGBA")

    # to increment base variables for pasting
    xincrement = 130
    yincrement = 93
    
    # base variables (week 0, monday)
    ybase = 148
    xbase = 70

    # paste the image in place (image, (x, y), color/mask)
    # week (y) modifier
    i = weeknumb

    # day (x modifier)
    #for j, day in enumerate(weekarray):
    #    if day:
    #        # if day == true paste tick, else print cross
    #        img.paste(tickimg, ((xbase + (xincrement*j)), ybase + (yincrement*i)), tickimg)
    #    else:
    #        img.paste(crossimg, ((xbase + (xincrement*j)), ybase + (yincrement*i)), crossimg)

    # crop the bottom off the final img - left pos of crop, top pos of crop, width of final img, height of final img
    img = img.crop((0, 0, 960, 600))

    img.save(imgpath)
    return(imgpath)