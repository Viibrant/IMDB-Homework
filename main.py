from imdb import IMDb
import bs4
import datetime
import random
import re
import requests
import sqlite3
import time
from tqdm import tqdm
ia = IMDb(adultSearch=False)
db = sqlite3.connect('usernames.db')
c = db.cursor()
# Initialise tables if they don't already exist
c.execute(
    "CREATE TABLE IF NOT EXISTS details(username TEXT, password TEXT, lastFilms TEXT, likedFilms TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS info(username TEXT, name TEXT, address TEXT, dateofbirth TEXT, gender TEXT, interests TEXT)")
db.commit()


# Changes ["spam", "eggs"] to "spam, eggs"
def listBeaut(ugly): return ', '.join(ugly)

def authLoop(expression, message):
    # prompts the user for input until a regex expression is not met
    variable = ''
    while not(re.compile(expression).match(''.join(sorted(variable)))):
        variable = input(message)
    return variable

def tryAttr(movie, variable):
    # checks if an attribute for a movie exists, catches any exceptions
    try:
        return str(movie[variable]) + "\n"
    except Exception as e:
        return ''

def getDetails(id):
    # Returns string about a film given the movie
    movie = ia.get_movie(id)
    title = "Name: " + \
        tryAttr(movie, "title") if tryAttr(movie, "title") != '' else ''
    year = "Year: " + \
        tryAttr(movie, "year") if tryAttr(movie, "year") != '' else ''
    url = "URL: "+ia.get_imdbURL(movie)+"\n"
    if tryAttr(movie, "genres") != '':
        genres = "Genres: " + listBeaut(movie["genres"]) + "\n"
    else:
        genres = ''
    if tryAttr(movie, "cast") != '':
        actors = 'Actors: ' + \
            listBeaut([(movie['cast'][x]['name'])
                       for x in range(len(movie['cast']))])
    else:
        actors = ''
    return("\n<film>\n" + title + url + year + genres + actors + "\n</film>\n")

def getRecommendations(id):
    # Returns IDs of recommended movies given a movie ID
    src = requests.get('http://www.imdb.com/title/tt{id}/'.format(id=id)).text
    bs = bs4.BeautifulSoup(src, "lxml")
    recs = [rec['data-tconst'][2:] for rec in bs.findAll('div', 'rec_item')]
    return recs

def getFilm():
    film = authLoop(r"^(?!\s*$).+", "Enter the name of a film\n> ")
    movies = ia.search_movie(film)
    for x in range(len(movies)):
        films = []; films.append(getDetails(movies[x-1].movieID))
        [print(film) for film in films]
        if int(authLoop(r"([1-3])", "Is this the film you mean? \n1) Yes\n2) No\n>.. ")) == 1:
            return movies[x-1].movieID

def register():
    while True:
        username = authLoop(
            r"^\w{4,}$", "Enter a username (greater than 3 chars)\n> ")
        c.execute("SELECT * FROM details WHERE username=?", (username,))
        result = c.fetchone()
        if result != None:
            print("Username already exists!")
            username = ''
        else:
            password = authLoop(r"^(?=.*\d).{4,}$",
                                "Enter a password. Your password must have at least 1 number and a capital letter\n> ")
            print("Because Rahman is an MI6 agent im gon need some details please owo")
            while True:
                try:
                    date_entry = input('Enter a date in YYYY-MM-DD format\n> ')
                    year, month, day = map(int, date_entry.split('-'))
                    date1 = datetime.date(year, month, day)
                except Exception as e:
                    if "month must be in 1..12" in str(e):
                        print("give me an actual date you twat")
                    elif "invalid literal for int()" in str(e) or "need more" in str(e):
                        print("give me the date in the actual format")
                    elif "year is out of range" in str(e):
                        print("man's so far in the future")
                    continue
                else:
                    print("gg date")
                    break
            name = authLoop(r"^\w{1,}$", "wot ur name??\n> ")
            address = authLoop(r"^\w{1,}$", "gib address pls\n> ")
            gender = ''
            while gender == '' or gender == "":
                gender = input("gib gender (dont enter attack helicopter or u gay\n> ")
            print("fine your gender is gay now lmao")
            gender = 'gay' if "helicopter" in gender.lower() else None
            interests = authLoop(r"^\w{4,}$", "give me some interests ;3\n> ")
            print(
                "Username: {username}\nPassword: {password}\nName: {name}\nAddress: {address}\nGender: {gender}\nInterests: {interests}"
                .format(username=username, password=password, name=name, address=address, gender=gender, interests=interests)
            )
            choice = authLoop(r"^[a-z]{1}$", "y or n?\n> ").lower()
            if choice == 'y':
                print("Registering..\n\n")
                c.execute("INSERT INTO details(username, password) VALUES(?,?)", (
                    username, password))
                c.execute("INSERT INTO info(username, name, address, dateofbirth, gender, interests) VALUES(?,?,?,?,?,?)",
                        username, name, address, date1, gender, interests)
                db.commit()
                break
            else:
                print("Cancelling..\n\n")
                break

def login():
    global username
    username = input("Username:\n> ")
    password = input("Password:\n> ")
    c.execute("SELECT * FROM DETAILS WHERE username=? AND password=?",
              (username, password))
    if c.fetchone() != None:
        print("Found\n\n")
        return True
    else:
        print("Whoops, that username/password combo was not found.")
        return False

def main_menu():
    c.execute("SELECT * from details WHERE username=?", (username,))
    existingFilms = c.fetchone()[2]
    if existingFilms == None:
        print("you haven't got any films ;//\nlets change that ᶘ ᵒᴥᵒᶅ")
        films = []
        for x in tqrb(range(10)):
            films.append(getFilm())
        print(films)
        c.execute("UPDATE details SET lastfilms= ? WHERE username=?",
                  (listBeaut(films), username))
        db.commit()
    # TODO retrieve account data
    while True:
        print("==== Main Menu ====\n1) Get Recommendations\n2) Like menu\n3) Get account data\n4) Log out")
        choice = int(authLoop(r"([1-4])", "> "))
        # Recommendations
        if choice == 1:
            while True:
                print(
                    "==== Recommendations ====\n1) Recommend via existing genres \n2) Recommend via a film\n3) Cancel")
                choice = int(authLoop(r"([1-3])", "> "))
                if choice == 1:
                    c.execute("SELECT * from details WHERE username='%s'" %
                            (username))
                    films = c.fetchall()
                    genres = []
                    error = False
                    for film in films:
                        ids = film[3].split(',')
                        for filmid in tqdm(ids):
                            try:
                                movie = ia.get_movie(str(filmid))
                            except Exception as e:
                                print("you have bad internet ;//"); print(e)
                                error = True; break
                            genres.append(movie["genre"])
                    else:
                        if error:
                            print("An error occurred ;/")
                            break
                        else:
                            genres = sum(genres, [])
                            print("Got genres")
                            time.sleep(0.25)
                            print("Getting related genres..")
                            results = ia.search_keyword(
                                random.choice(genres), results=5)
                            print("Getting some films from genres you've watched..")
                            films = []
                            for x in tqdm(range(5)):
                                returnedFilms = ia.get_keyword(
                                    random.choice(results))
                                film = random.choice(returnedFilms)
                                films.append(getDetails(film.movieID))
                            [print(film) in films for film in films]
                if choice == 2:
                    recommendations = getRecommendations(getFilm())
                    for x in range(5 if len(recommendations) < 5 else len(recommendations)): getDetails(recommendations[x-1])
                if choice == 3: choice = ''; break
        # Like Menu
        if choice == 2:
            while True:
                print("==== Likes ====\n1) View List\n2) Like a film\n3) Exit")
                choice = int(authLoop(r"([1-3])", "> "))
                if choice == 3: choice = ''; break
                if choice == 1:
                    c.execute("SELECT likedFilms FROM details WHERE username=?", (username,)) 
                    result = c.fetchone()
                    if result == None:
                        print("No liked films!")
                    else:
                        films = []
                        for id in tqdm(''.join(c for c in result if c not in '()').split(',')):
                            films.append(getDetails(id))
                        [print(film) for film in films]
                if choice == 2:
                    movieID = getFilm()
                    c.execute("SELECT likedFilms FROM details WHERE username=?", (username,))
                    result = list(c.fetchone())
                    result.append(movieID)
                    c.execute("UPDATE details SET likedFilms= ? WHERE username=?", (listBeaut(result), username))
        if choice == 3:
            time.sleep(1); print("==== Details ====\nthis is in compliance with the eu data laws or smth idk lmao")
            c.execute("SELECT * FROM info WHERE username=?", (username,))
            result = c.fetchone()
            time.sleep(1); 
            print("Username: {username}\nName: {name}\nAddress: {address}\nDate of Birth: {DoB}\nGender: {gender}\nInterests: {interests}\n".format(
                username=result[0], name=result[1], address=result[2], DoB=result[3], gender=result[4], interests=result[5]
            ))
        # Logout
        if choice == 4:
            break

print("Welcome!\n")
if __name__ == "__main__":
    while True:
        print("\n==== Start Menu ====\n1) Login\n2) Register\n3) Exit")
        choice = int(authLoop(r"([1-3])", "> "))
        if choice == 1:
            if login() == True:
                print("Welcome back!")
                main_menu()
        register() if choice == 2 else exit() if choice == 3 else None

