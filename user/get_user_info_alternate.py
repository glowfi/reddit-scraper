import random
from helper.utils import (
    epoch_age,
    generate_random_epoch,
    generate_random_hex_color,
    getDate,
    success,
)
from user.utils import generate_colors, generate_description


async def getRedditorInfoAlternate(aid, userInfo, profilePics, total_users):
    val = generate_random_epoch()
    age = epoch_age(val)
    date = getDate(val)
    primary, key = generate_colors()

    # randomize_profile_pic = random.sample(profilePics, 1)[0]
    # hexColor = f'#{randomize_profile_pic["hex"]}'
    # dat = randomize_profile_pic["data"]
    # avatar_img = random.sample(dat, 1)[0]

    randomize_profile_pic = random.sample(profilePics, 1)[0]
    avatar_img = randomize_profile_pic
    hexColor = generate_random_hex_color()

    userInfo[aid]["cakeDay"] = val
    userInfo[aid]["cakeDayHuman"] = date
    userInfo[aid]["age"] = age
    userInfo[aid]["avatar_img"] = avatar_img
    userInfo[aid]["banner_img"] = ""
    userInfo[aid]["publicDescription"] = generate_description()
    userInfo[aid]["over18"] = False
    userInfo[aid]["keycolor"] = key
    userInfo[aid]["primarycolor"] = primary
    userInfo[aid]["iconcolor"] = hexColor
    userInfo[aid]["supended"] = False
    total_users[0] -= 1
    success(f"More {total_users} left ...")
