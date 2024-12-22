# Import necessary modules
import requests, sqlite3, os, inquirer, base64, traceback

# Vars
user = ''
dbpath = ''
dim = ''
auth = ''
covpath = ''
bannpath = ''

# Main function
def main():
    global user, dbpath, dim, auth
    print("Welcome " + user + " to Lutris Cover Art Downloader!\n")
    user = GetUser()
    dbpath = '/home/' + user + '/.local/share/lutris/pga.db'
    dim = GetCoverType()
    auth = GetAPIKey()
    print("Getting API Key...\n")
    if auth == '':
        SetAPIKey()
    co = DBConnect()
    GetGamesList(co)
    CleanNotInstalledGames(co)

####### FUNCTIONS

#Get list of installed games
def CleanNotInstalledGames(co):
    c = co.execute('SELECT slug FROM games WHERE installed = "1"')
    games = c.fetchall()
    listgames = []
    for entry in games:
        title = entry[0] + '.jpg'
        listgames.append(title.lower())
    DeleteImages(listgames)

def DeleteDirs():
    covpath = '/home/' + user + '/.cache/lutris/coverart/'
    bannpath = '/home/' + user + '/.cache/lutris/banners/'
    for path in [covpath,bannpath]:
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            try:
                print("Deleting "+file_path)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Exception occured deleting %s. Reason: %s' % (file_path, e))

#Delete covers/banners for not installed games
def DeleteImages(listgames):
    covpath = '/home/' + user + '/.cache/lutris/coverart/'
    bannpath = '/home/' + user + '/.cache/lutris/banners/'
    os.makedirs(covpath, exist_ok=True)
    os.makedirs(bannpath, exist_ok=True)
    for path in [bannpath, covpath]:
        for filename in os.listdir(path):
            try:
                if filename.lower() not in listgames and os.path.isfile(os.path.join(path, filename)):
                    if filename.lower().endswith('.jpg'):
                        os.remove(os.path.join(path, filename))
            except:
                print("An exception occured deleting "+filename)


def GetUser():
    try:
        return os.getlogin()
    except:
        print("Could not get session username")
        exit(1)

def GetCoverType():
    global covpath
    global bannpath
    questions = [
    inquirer.List('type',
                    message="Would you like to download Steam banners or Steam vertical covers?",
                    choices=['Banner (460x215)', 'Vertical (600x900)', 'Both (600x900 920x430)',
                            'I\'m Feeling lucky!'
                             ],
                ),
    ]
    ans = inquirer.prompt(questions)["type"]
    print('Cover type set to ' + ans + '\n')
    if ans == 'Banner (460x215)':
        covpath = '/home/' + user + '/.cache/lutris/banners/'
        dim = '460x215'
    elif ans == 'Vertical (600x900)':
        covpath = '/home/' + user + '/.cache/lutris/coverart/'
        dim = '600x900'
    elif ans == 'Both (600x900 920x430)' :
        covpath = '/home/' + user + '/.cache/lutris/coverart/'
        bannpath = '/home/' + user + '/.cache/lutris/banners/'
        dim = 'both'
    else :
        covpath = '/home/' + user + '/.cache/lutris/coverart/'
        bannpath = '/home/' + user + '/.cache/lutris/banners/'
        dim = 'random'
    return dim

def SaveAPIKey(key):
    with open('./apikey.txt', 'w') as f:
        f.write(key)

def GetAPIKey():
    if os.path.isfile('./apikey.txt'):
        with open('./apikey.txt', 'r') as f:
            key = f.read()
            auth = {'Authorization': 'Bearer ' + key}
            return auth
    else:
        return ''

def SetAPIKey():
    print("Could not find API key")
    print('You need a SteamGriDB API key to use this script.')
    print('You can get one by using your Steam account and heading here: https://www.steamgriddb.com/profile/preferences/api\n')
    api = input("Enter your SteamGridDB API key: ")
    auth = {'Authorization': 'Bearer ' + api}
    TestAPI(auth, api)

def TestAPI(key, api):
    r = requests.get('https://www.steamgriddb.com/api/v2/grids/game/1?dimensions=600x900', headers=key)
    if r.status_code == 200:
        print("API key is valid, saving...")
        SaveAPIKey(api)
    else:
        print("API key is invalid")
        exit(1)

def DBConnect():
    try:
        conn = sqlite3.connect(dbpath)
    except:
        print("Could not find Lutris database 'pga.db'. You can manually edit script's path if necessary")
        exit(1)
    return conn

# Search for a game by name via Lutris database, then get the grid data
def SearchGame(game):
    print(game)
    res = requests.get('https://www.steamgriddb.com/api/v2/search/autocomplete/' + game, headers=auth).json()
    if len(res["data"]) == 0:
        print("Could not find a cover for game " + game)
    else:
        print("Found game " + game.replace('-', ' ').title())
        id = res["data"][0]["id"]
        return id

# Download cover by searching for the game via its name, then via its SteamGriDB's ID
def DownloadCover(name):
    from random import randint as randint
    try:
        gameid = SearchGame(name)
        if dim == 'random':
            rand = randint(0,20)
            dice = randint(0,5)
            dim1 = '920x430'
            dim1ALT = '460x215'
            dim2 = '600x900'
            r = rand
            while True and r>=0:
                try:
                    if r != rand:
                        print("Retrying banner for " + name.replace('-', ' ').title())
                    else:
                        print("Downloading banner for " + name.replace('-', ' ').title())
                    grid1 = requests.get('https://www.steamgriddb.com/api/v2/grids/game/' + str(gameid) + '?dimensions=' + dim1, headers=auth).json()
                    url1 = grid1["data"][r]["url"]
                    print("%s %s | %s" % (chr(0x2680+dice), r, url1.split('/')[-1]))
                    break
                except:
                    r = randint(0,r)
                    print("Could not find a banner for game " + name)
                    print(traceback.format_exc())
            r=rand
            while r>=0:
                try:
                    if r != rand:
                        print("Retrying cover for " + name.replace('-', ' ').title())
                    else:
                        print("Downloading cover for " + name.replace('-', ' ').title())
                    grid2 = requests.get('https://www.steamgriddb.com/api/v2/grids/game/' + str(gameid) + '?dimensions=' + dim2, headers=auth).json()
                    url2 = grid2["data"][r]["url"]
                    print("%s %s | %s" % (chr(0x2680+dice), r, url2.split('/')[-1]))
                    break
                except:
                    r = randint(0,r)
                    print("Could not find a cover for game " + name)
                    print(traceback.format_exc())
            r1 = requests.get(url1)
            r2 = requests.get(url2)
            ext1 = url1.split('.')[-1]
            ext2 = url2.split('.')[-1]
            os.makedirs(covpath, exist_ok=True)
            os.makedirs(bannpath, exist_ok=True)
            with open(bannpath + name + '.'+ext1, 'wb') as f1:
                f1.write(r1.content)
            with open(covpath + name + '.'+ext2, 'wb') as f2:
                f2.write(r2.content)
        elif dim == 'both':
            print("Downloading cover and banner for " + name.replace('-', ' ').title())
            dim1 = '920x430'
            dim1ALT = '460x215'
            dim2 = '600x900'
            while True:
                try:
                    grid1 = requests.get('https://www.steamgriddb.com/api/v2/grids/game/' + str(gameid) + '?dimensions=' + dim1, headers=auth).json()
                    url1 = grid1["data"][0]["url"]
                except:
                    if dim1 == dim1ALT:
                        break
                    dim1 = dim1ALT
                    print("Could not find a banner for game " + name)
                    return
                break
            try:
                grid2 = requests.get('https://www.steamgriddb.com/api/v2/grids/game/' + str(gameid) + '?dimensions=' + dim2, headers=auth).json()
                url2 = grid2["data"][0]["url"]
            except:
                print("Could not find a cover for game " + name)
                return
            r1 = requests.get(url1)
            r2 = requests.get(url2)
            os.makedirs(covpath, exist_ok=True)
            os.makedirs(bannpath, exist_ok=True)
            with open(bannpath + name + '.jpg', 'wb') as f1:
                f1.write(r1.content)
            with open(covpath + name + '.jpg', 'wb') as f2:
                f2.write(r2.content)
        else :
            print("Downloading cover for " + name.replace('-', ' ').title())
            grids = requests.get('https://www.steamgriddb.com/api/v2/grids/game/' + str(gameid) + '?dimensions=' + dim, headers=auth).json()
            try:
                url = grids["data"][0]["url"]
            except:
                print("Could not find a cover for game " + name)
                return
            r = requests.get(url)
            os.makedirs(covpath, exist_ok=True)
            with open(covpath + name + '.jpg', 'wb') as f:
                f.write(r.content)
    except:
        print("An exception occurred fetching "+name)
        print(traceback.format_exc())

# Get all games and for each game, check if it already has a cover
def GetGamesList(co):
    c = co.execute('SELECT slug FROM games WHERE installed = "1"')
    games = c.fetchall()
    if dim == 'random':
        DeleteDirs()
    for entry in games:
        title = entry[0]
        if dim == 'random' or not os.path.isfile(covpath + title + '.jpg'):
            # If not, download it
            DownloadCover(title)
        else:
            print("Cover for " + title.replace('-', ' ').title() + " already exists")
    print('All done ! Restart Lutris for the changes to take effect')

if __name__ == '__main__':
    main()
