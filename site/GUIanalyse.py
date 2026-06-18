from PIL import Image
import json
from datetime import datetime
import hashlib
import os



def isImg(path):
	try:
		with Image.open(path) as img:
			img.verify()
		return True
	except Exception:
		return False

def atomic_write(filepath, data):
    tmp_path = filepath + ".tmp"

    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(tmp_path, filepath)  # remplace de façon atomique


def push_to_data(auteur,email,titre,image_path,accord,c1,c2,c3,preuve=None,titre_analyse=None):

	index = json.load(open(os.path.join(SITE, "index.json")))


	last_id = index["analyses"][-1]["id"] if index["analyses"] else "000"
	n = int(last_id) + 1
	s = str(n).zfill(3)

	date_now = datetime.now().date().isoformat()
	filename = os.path.basename(image_path)
	web_path = f"images/{filename}"
	entry = {
		"id": s,
		"date": date_now,
		"auteur": auteur,
		"email": email,
		"titre": titre,
		"image_local": web_path,
		"image_cloudinary": "",
		"accord": accord,
		"preuve": preuve or "",
		"hash": hash_data(auteur,email,titre,accord,date_now,preuve),
		"status": "published",
		"titre_analyse": titre_analyse,
		"c1": c1,
		"c2": c2,
		"c3": c3
	}
	atomic_write(os.path.join(SITE, f"data/{s}.json"), {"data": [entry]})
	return s

def push_to_index(id,cat):
	f = os.path.join(SITE, "index.json")
	d=json.load(open(f))
	s=str(id).zfill(3)

	data = json.load(open(os.path.join(SITE, f"data/{s}.json")))
	h=data["data"][0]["hash"]

	d["analyses"].append({
		"id":s,
		"hash":h,
		"cat":cat
	})
	atomic_write(f, d)

def get_data(qid):
	for item in queue["queue"]:
		if item["id"] == qid:
			return (
				item["auteur"],
				item["email"],
				item["titre"],
				item["image_local"],
				item["accord"],
				item.get("preuve")
			)
	return None

def selectAnalyse():

	file = input("Entrez le path de votre image :\n> ").strip().strip("'").strip('"')

	if not isImg(file):
		print("Erreur")
		return

	auteur = input("Auteur ?\n> ")
	email = input("Email ?\n> ")
	titre = input("Titre ?\n> ")
	accord = input("Accord ? (true/false)\n> ")

	add_to_queue(auteur, email, titre, file, accord)

	print("> Ajouté à la queue")
	return load_queue()

def delete(queue):
	if not queue["queue"]:
		print("Queue vide")
		return

	queue["queue"].pop(0)
	save_queue(queue)
	return load_queue()
	
def cancel(inpt):
	if inpt == 'c':
		loop = True
		return loop

def standby(queue):
	if not queue["queue"]:
		print("Queue vide")
		return

	r = input('Voulez-vous laisser une note ? (y/n)\n> ')

	if r == 'y':
		note = input('Quelle note voulez vous laisser ?\n> ')
		queue["queue"][0]["note"] = note

	elif r == 'n':
		item = queue["queue"].pop(0)
		queue["queue"].append(item)

	save_queue(queue)
	print('Standby effectué.')
	return load_queue()


def analyze(queue):

	if not queue["queue"]:
		print("Queue vide")
		return

	item = queue["queue"][0]

	titre_analyse = input("> titre analyse : ")
	c1 = input("> C1 : ")
	c2 = input("> C2 : ")
	c3 = input("> C3 : ")
	cat = input("> catégorie : ")
	new_id_created = push_to_data(
		item["auteur"],
		item["email"],
		item["titre"],
		item["image_local"],
		item["accord"],
		c1,
		c2,
		c3,
		item.get("preuve"),
		titre_analyse
	)

	push_to_index(new_id_created, cat)

	queue["queue"].pop(0)
	save_queue(queue)
	print("done")
	return load_queue()

def idAnalyze(queue):

	while True:
		try:
			i = int(input('> id ?\n> '))
			break
		except ValueError:
			pass

	if i >= len(queue["queue"]):
		print("ID invalide")
		return

	item = queue["queue"][i]

	titre_analyse = input("> titre analyse : ")
	c1 = input("> C1 : ")
	c2 = input("> C2 : ")
	c3 = input("> C3 : ")
	cat = input("> catégorie : ")

	new_id_created = push_to_data(
		item["auteur"],
		item["email"],
		item["titre"],
		item["image_local"],
		item["accord"],
		c1,
		c2,
		c3,
		item.get("preuve"),
		titre_analyse
	)

	push_to_index(new_id_created, cat)

	queue["queue"].pop(i)
	save_queue(queue)

	print("done")
	return load_queue()

def load_queue():
	# Fonction qui charge la queue
	try:
		with open('queue.json', 'r')as f:
			return json.load(f)
	except FileNotFoundError:
		return {'queue': []}

def hash_data(auteur, email, titre, accord, date, preuve=None):
	# Hashage 3 étapes
	data_to_hash = f"{auteur}|{email}|{titre}".encode()
	security_hash = f"{accord}|{date}".encode()
	proof_hash = f"{preuve}".encode()

	hashed_data = hashlib.sha256(data_to_hash).hexdigest()
	hashed_security = hashlib.sha256(security_hash).hexdigest()
	proof_hashed = hashlib.sha256(proof_hash).hexdigest()

	final_hash = f"{hashed_data}|{hashed_security}|{proof_hashed}".encode()
	hashed = hashlib.sha256(final_hash).hexdigest()
	print(hashed)
	return hashed

def is_h_right(h):
	if h == 'ef573f31e35ca9b276d1d9b36720423cc2fe48f3d06a68d7ea03306052ee2dda':
		print('\n')
		return True
def save_queue(data):
	#Fonction permettant de sauvegarder dans la queue
	atomic_write("queue.json", data)
		
def add_to_queue(auteur, email, titre, image_path, accord, preuve=None,note=None):
	# Fonction permettant d'ajouter une entrée à la queue manuellement
	data = load_queue()
	date_now = datetime.now().isoformat()
	entry = { 
		"id": f"q{str(len(data['queue'])+1).zfill(3)}",
		"date": date_now,
		"auteur":auteur,
		"email": email,
		"titre": titre,
		"image_local": image_path,
		"accord": accord,
		"preuve":preuve,
		"hash": hash_data(auteur, email, titre, accord, date_now, preuve),
		"note":"",
		"status":"pending"
		}

	data["queue"].append(entry)
	save_queue(data)
	return load_queue()

def display_queue(tqueue):
	# Fonction qui print la queue à l'instant t dans le terminal
    print("\n=== FILE D'ATTENTE ===")

    if not tqueue["queue"]:
        print("La file est vide.")
        return

    for item in tqueue["queue"]:
        print(f"""
ID : {item['id']}
Titre : {item['titre']}
Image : {item['image_local']}
-------------------------
""")

def sync():
    files = [f for f in os.listdir() if f.endswith(".json") and f[:3].isdigit()]
    files.sort()

    new_index = {"analyses": []}

    for file in files:
        try:
            with open(file, "r") as f:
                data = json.load(f)

            entry = data["data"][0]

            # recalcul hash
            new_hash = hash_data(
                entry["auteur"],
                entry["email"],
                entry["titre"],
                entry["accord"],
                entry["date"],
                entry.get("preuve")
            )

            # update hash dans fichier
            entry["hash"] = new_hash

            # rewrite fichier propre
            atomic_write(file, {"data": [entry]})

            # rebuild index
            new_index["analyses"].append({
                "id": entry["id"],
                "hash": new_hash,
                "cat": entry.get("cat", "unknown")
            })

        except Exception as e:
            print(f"Erreur avec {file}: {e}")

    # rewrite index
    atomic_write("index.json", new_index)

    print("Sync terminé.")

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "site")


h = True
while h is not True:
	TTD = input('Bienvenue')
	if TTD == 'sh':
		auteur = input('Auteur ?')
		date = input('date ?')	
		email = input("Email ?")
		titre = input('Titre ?')
		accord = input('Accord ?')
		preuve = input('Preuve ?')
		h = hash_data(auteur, email, titre, date, accord, preuve)
		h = is_h_right(h)

CAF = True
queue = load_queue()

while CAF is True:
#	print('\n ',queue, "Voici la file d'attente")
	AAF = input('Bienvenue, que souhaitez vous faire ?\n> ')

	if AAF == 'a':
		queue = analyze(queue)

	elif AAF == 's':
		queue = standby(queue)

	elif AAF  == 'd':
		queue = delete(queue)
	elif AAF == 'sa':
		queue = selectAnalyse()
	elif AAF == 'ia':
		queue = idAnalyze(queue)
	elif AAF == 'dq':
		display_queue(queue)
	elif AAF == 'sh':
		auteur = input('Auteur ?')
		date = input('date ?')
		email = input("Email ?")
		titre = input('Titre ?')
		accord = input('Accord ?')
		preuve = input('Preuve ?')
		hash_data(auteur, email, titre, date, accord, preuve)
	elif AAF == 'sync':
		sync()
	elif AAF == 'h':
		print('a -> Analyze\ns -> Standby\nd -> Delete\nsa -> Select Analyze\nia -> ID Analyze')